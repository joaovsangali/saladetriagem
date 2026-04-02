import random
import secrets
from datetime import datetime, timedelta, timezone

from flask import render_template, redirect, url_for, flash, request, current_app, session
from markupsafe import Markup
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.auth import auth_bp
from app.models import PoliceUser, UserSession, SMSVerification, GlobalSMSCounter
from app.extensions import db, limiter
from app.mail import send_confirmation_email


def _create_user_session(user):
    """Invalidate all previous sessions and create a new one. Returns token."""
    UserSession.query.filter_by(user_id=user.id, is_active=True).update(
        {'is_active': False}, synchronize_session=False
    )
    token = secrets.token_urlsafe(32)
    user_session = UserSession(
        user_id=user.id,
        session_token=token,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent', '')[:256],
    )
    db.session.add(user_session)
    db.session.commit()
    session['user_session_token'] = token
    return token


def _get_or_create_sms_counter(month: str) -> GlobalSMSCounter:
    counter = GlobalSMSCounter.query.filter_by(month=month).first()
    if not counter:
        counter = GlobalSMSCounter(month=month, count=0)
        db.session.add(counter)
        db.session.flush()
    return counter


def _send_sms_verification(user) -> bool:
    """Generate and send SMS code. Returns True if sent or limit reached gracefully."""
    month = datetime.now(timezone.utc).strftime('%Y-%m')
    limit = current_app.config.get('GLOBAL_SMS_LIMIT_PER_MONTH', 100)

    counter = _get_or_create_sms_counter(month)
    if counter.count >= limit:
        flash(
            'Limite global de SMS atingido este mês. Tente novamente no próximo mês ou '
            'entre em contato com o suporte.',
            'warning',
        )
        db.session.commit()
        return False

    code = str(random.randint(100000, 999999))
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    verification = SMSVerification(
        phone=user.phone,
        code=code,
        expires_at=expires_at,
    )
    db.session.add(verification)

    counter.count += 1
    db.session.commit()

    from app.sms import get_sms_provider
    provider = get_sms_provider()
    provider.send(user.phone, f'Sala de Triagem: seu código de verificação é {code}. Válido por 10 minutos.')
    return True


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = PoliceUser.query.filter_by(email=email, is_active=True).first()
        if user and user.check_password(password):
            login_user(user, remember=False)
            _create_user_session(user)

            # Redirect to phone verification if not yet verified
            if user.phone and not user.phone_verified_at:
                _send_sms_verification(user)
                return redirect(url_for("auth.verify_phone"))

            return redirect(url_for("dashboard.index"))
        flash("E-mail ou senha inválidos.", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    # Invalidate user session record
    token = session.get('user_session_token')
    if token:
        user_session = UserSession.query.filter_by(
            session_token=token, user_id=current_user.id
        ).first()
        if user_session:
            user_session.is_active = False
            db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))


def _make_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        terms = request.form.get("terms")

        errors = []
        if not display_name:
            errors.append("Nome completo é obrigatório.")
        if not phone:
            errors.append("Telefone é obrigatório.")
        if not email:
            errors.append("E-mail é obrigatório.")
        if not password:
            errors.append("Senha é obrigatória.")
        elif len(password) < 8:
            errors.append("A senha deve ter pelo menos 8 caracteres.")
        if password != password_confirm:
            errors.append("As senhas não conferem.")
        if not terms:
            errors.append("Você deve aceitar os Termos de Serviço.")

        if not errors and PoliceUser.query.filter_by(email=email).first():
            errors.append("E-mail já cadastrado.")

        if not errors and phone:
            from app.utils.validators import normalize_phone
            phone_normalized = normalize_phone(phone)
            existing_users = PoliceUser.query.with_entities(PoliceUser.phone).all()
            for (existing_phone,) in existing_users:
                if existing_phone and normalize_phone(existing_phone) == phone_normalized:
                    errors.append("Telefone já cadastrado.")
                    break

        if errors:
            for msg in errors:
                flash(msg, "danger")
            return render_template(
                "auth/register.html",
                form_data=request.form,
            )

        # Anti-abuse: check if phone was previously used in a trial
        trial_days = current_app.config.get('TRIAL_DURATION_DAYS', 30)
        phone_had_trial = PoliceUser.query.filter(
            PoliceUser.phone == phone,
            PoliceUser.trial_ends_at.isnot(None),
        ).first()

        if phone_had_trial:
            # Phone was used in a previous trial — start as free
            plan_type = 'free'
            trial_ends_at = None
        else:
            plan_type = 'trial'
            trial_ends_at = datetime.now(timezone.utc) + timedelta(days=trial_days)

        user = PoliceUser(
            email=email,
            display_name=display_name,
            phone=phone or None,
            is_active=False,
            plan_type=plan_type,
            trial_ends_at=trial_ends_at,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        s = _make_serializer()
        token = s.dumps(email, salt="email-confirm")
        confirm_url = url_for("auth.confirm_email", token=token, _external=True)
        sent = send_confirmation_email(email, confirm_url)

        if sent:
            flash(
                "Cadastro realizado! Verifique seu e-mail para ativar a conta.",
                "success",
            )
        else:
            flash(
                Markup(
                    "Cadastro realizado! O envio do e-mail falhou (SMTP não configurado). "
                    f'Acesse o link para ativar sua conta: <a href="{confirm_url}">{confirm_url}</a>'
                ),
                "warning",
            )
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/register.html",
        form_data={},
    )


@auth_bp.route("/confirm/<token>")
@limiter.limit("30 per minute")
def confirm_email(token):
    s = _make_serializer()
    max_age = current_app.config.get("CONFIRMATION_TOKEN_MAX_AGE", 86400)
    try:
        email = s.loads(token, salt="email-confirm", max_age=max_age)
    except SignatureExpired:
        return render_template("auth/confirm_expired.html"), 410
    except BadSignature:
        return render_template("auth/confirm_expired.html"), 400

    user = PoliceUser.query.filter_by(email=email).first()
    if user is None:
        return render_template("auth/confirm_expired.html"), 404

    if user.is_active:
        flash("Conta já confirmada. Faça login.", "info")
        return redirect(url_for("auth.login"))

    user.is_active = True
    db.session.commit()
    return render_template("auth/confirm_ok.html")


@auth_bp.route("/resend-confirmation", methods=["POST"])
@limiter.limit("5 per minute")
def resend_confirmation():
    email = request.form.get("email", "").strip().lower()
    user = PoliceUser.query.filter_by(email=email, is_active=False).first()
    if user:
        s = _make_serializer()
        token = s.dumps(email, salt="email-confirm")
        confirm_url = url_for("auth.confirm_email", token=token, _external=True)
        sent = send_confirmation_email(email, confirm_url)
        if sent:
            flash(
                "Um novo link de confirmação foi enviado para o seu e-mail.",
                "info",
            )
        else:
            flash(
                Markup(
                    "SMTP não configurado. "
                    f'Acesse o link para ativar sua conta: <a href="{confirm_url}">{confirm_url}</a>'
                ),
                "warning",
            )
        return redirect(url_for("auth.login"))
    flash(
        "Se o e-mail estiver pendente de confirmação, um novo link foi enviado.",
        "info",
    )
    return redirect(url_for("auth.login"))


@auth_bp.route("/verify-phone", methods=["GET"])
@login_required
def verify_phone():
    if current_user.phone_verified_at:
        return redirect(url_for("dashboard.index"))

    # Check resend cooldown (last verification created in the last 60s)
    last = (
        SMSVerification.query.filter_by(phone=current_user.phone)
        .order_by(SMSVerification.created_at.desc())
        .first()
    )
    resend_available_in = None
    if last and not last.is_expired:
        elapsed = (datetime.now(timezone.utc) - last.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        cooldown = 60
        if elapsed < cooldown:
            resend_available_in = int(cooldown - elapsed)

    return render_template(
        "account/verify_phone.html",
        resend_available_in=resend_available_in,
    )


@auth_bp.route("/verify-phone", methods=["POST"])
@login_required
@limiter.limit("10 per minute")
def verify_phone_submit():
    if current_user.phone_verified_at:
        return redirect(url_for("dashboard.index"))

    code = request.form.get("code", "").strip()

    verification = (
        SMSVerification.query.filter_by(phone=current_user.phone)
        .order_by(SMSVerification.created_at.desc())
        .first()
    )

    if not verification or verification.is_expired or verification.is_verified:
        flash("Código inválido ou expirado. Solicite um novo código.", "danger")
        return redirect(url_for("auth.verify_phone"))

    verification.attempts += 1
    if verification.attempts > 5:
        db.session.commit()
        flash("Muitas tentativas incorretas. Solicite um novo código.", "danger")
        return redirect(url_for("auth.verify_phone"))

    if verification.code != code:
        db.session.commit()
        flash("Código incorreto. Tente novamente.", "danger")
        return redirect(url_for("auth.verify_phone"))

    verification.verified_at = datetime.now(timezone.utc)
    current_user.phone_verified_at = datetime.now(timezone.utc)
    db.session.commit()

    flash("Telefone verificado com sucesso!", "success")
    return redirect(url_for("dashboard.index"))


@auth_bp.route("/verify-phone/resend", methods=["POST"])
@login_required
@limiter.limit("3 per minute")
def resend_sms():
    if current_user.phone_verified_at:
        return redirect(url_for("dashboard.index"))

    if not current_user.phone:
        flash("Nenhum telefone cadastrado.", "warning")
        return redirect(url_for("dashboard.index"))

    # Cooldown check
    last = (
        SMSVerification.query.filter_by(phone=current_user.phone)
        .order_by(SMSVerification.created_at.desc())
        .first()
    )
    if last and not last.is_expired:
        elapsed = (datetime.now(timezone.utc) - last.created_at.replace(tzinfo=timezone.utc)).total_seconds()
        if elapsed < 60:
            flash(f"Aguarde {int(60 - elapsed)} segundo(s) antes de reenviar.", "warning")
            return redirect(url_for("auth.verify_phone"))

    _send_sms_verification(current_user)
    flash("Novo código enviado.", "info")
    return redirect(url_for("auth.verify_phone"))

