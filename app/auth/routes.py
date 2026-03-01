from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from app.auth import auth_bp
from app.models import PoliceUser
from app.extensions import db, limiter
from app.mail import send_confirmation_email

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
            return redirect(url_for("dashboard.index"))
        flash("E-mail ou senha inválidos.", "danger")
    
    return render_template("auth/login.html")

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


def _make_serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    require_cpf = current_app.config.get("REQUIRE_CPF_FOR_SIGNUP", False)

    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        cpf = request.form.get("cpf", "").strip()
        phone = request.form.get("phone", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        terms = request.form.get("terms")

        errors = []
        if not display_name:
            errors.append("Nome completo é obrigatório.")
        if require_cpf and not cpf:
            errors.append("CPF é obrigatório.")
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

        if errors:
            for msg in errors:
                flash(msg, "danger")
            return render_template(
                "auth/register.html",
                require_cpf=require_cpf,
                form_data=request.form,
            )

        user = PoliceUser(
            email=email,
            display_name=display_name,
            phone=phone or None,
            cpf=cpf or None,
            is_active=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        s = _make_serializer()
        token = s.dumps(email, salt="email-confirm")
        confirm_url = url_for("auth.confirm_email", token=token, _external=True)
        send_confirmation_email(email, confirm_url)

        flash(
            "Cadastro realizado! Verifique seu e-mail para ativar a conta.",
            "success",
        )
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/register.html",
        require_cpf=require_cpf,
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
        send_confirmation_email(email, confirm_url)
    flash(
        "Se o e-mail estiver pendente de confirmação, um novo link foi enviado.",
        "info",
    )
    return redirect(url_for("auth.login"))

