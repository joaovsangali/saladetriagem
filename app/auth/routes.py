from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.models import PoliceUser
from app.extensions import limiter, db, mail
import logging

logger = logging.getLogger(__name__)

def _get_serializer():
    from flask import current_app
    from itsdangerous import URLSafeTimedSerializer
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])

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
            if not user.email_confirmed:
                flash("Confirme seu e-mail antes de fazer login.", "warning")
                return redirect(url_for("auth.login"))
            login_user(user, remember=False)
            return redirect(url_for("dashboard.index"))
        flash("E-mail ou senha inválidos.", "danger")
    
    return render_template("auth/login.html")

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    from flask import current_app
    if not current_app.config.get("REGISTRATION_ENABLED", True):
        flash("O cadastro está desabilitado.", "warning")
        return redirect(url_for("auth.login"))
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    
    if request.method == "POST":
        display_name = request.form.get("display_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        cpf = request.form.get("cpf", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        terms_accepted = request.form.get("terms_accepted")

        if not display_name or not email or not password:
            flash("Preencha todos os campos obrigatórios.", "danger")
            return render_template("auth/register.html")
        if password != confirm_password:
            flash("As senhas não coincidem.", "danger")
            return render_template("auth/register.html")
        if len(password) < 8:
            flash("A senha deve ter no mínimo 8 caracteres.", "danger")
            return render_template("auth/register.html")
        if not terms_accepted:
            flash("Você deve aceitar os termos de uso.", "danger")
            return render_template("auth/register.html")
        if PoliceUser.query.filter_by(email=email).first():
            flash("E-mail já cadastrado.", "danger")
            return render_template("auth/register.html")

        user = PoliceUser(
            email=email,
            display_name=display_name,
            cpf=cpf,
            phone=phone,
            email_confirmed=False,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        _send_confirmation_email(user)
        flash("Verifique seu e-mail para confirmar o cadastro.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/confirm/<token>")
def confirm_email(token):
    try:
        s = _get_serializer()
        email = s.loads(token, salt="email-confirm", max_age=3600)
    except Exception:
        flash("Link de confirmação inválido ou expirado.", "danger")
        return redirect(url_for("auth.login"))
    
    user = PoliceUser.query.filter_by(email=email).first()
    if not user:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("auth.login"))
    if user.email_confirmed:
        flash("E-mail já confirmado. Faça login.", "info")
        return redirect(url_for("auth.login"))
    
    user.email_confirmed = True
    db.session.commit()
    flash("E-mail confirmado com sucesso! Faça login.", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = PoliceUser.query.filter_by(email=email, is_active=True).first()
        if user and user.email_confirmed:
            _send_reset_email(user)
        flash("Se esse e-mail estiver cadastrado, você receberá um link para redefinir sua senha.", "info")
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")

@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        s = _get_serializer()
        email = s.loads(token, salt="password-reset", max_age=3600)
    except Exception:
        flash("Link de redefinição inválido ou expirado.", "danger")
        return redirect(url_for("auth.login"))
    
    user = PoliceUser.query.filter_by(email=email, is_active=True).first()
    if not user:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for("auth.login"))
    
    if request.method == "POST":
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not password or len(password) < 8:
            flash("A senha deve ter no mínimo 8 caracteres.", "danger")
            return render_template("auth/reset_password.html", token=token)
        if password != confirm_password:
            flash("As senhas não coincidem.", "danger")
            return render_template("auth/reset_password.html", token=token)
        user.set_password(password)
        db.session.commit()
        flash("Senha redefinida com sucesso! Faça login.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("auth/reset_password.html", token=token)

def _send_confirmation_email(user):
    from flask import current_app
    from flask_mail import Message
    try:
        s = _get_serializer()
        token = s.dumps(user.email, salt="email-confirm")
        confirm_url = url_for("auth.confirm_email", token=token, _external=True)
        msg = Message(
            subject="Confirme seu cadastro — Sala de Triagem",
            recipients=[user.email],
            html=(
                f"<p>Olá, {user.display_name}!</p>"
                f"<p>Clique no link abaixo para confirmar seu e-mail:</p>"
                f"<p><a href='{confirm_url}'>{confirm_url}</a></p>"
                f"<p>O link expira em 1 hora.</p>"
                f"<hr><p><small>Este NÃO é um sistema oficial.</small></p>"
            ),
        )
        mail.send(msg)
    except Exception:
        logger.exception("Failed to send confirmation email to %s", user.email)

def _send_reset_email(user):
    from flask_mail import Message
    try:
        s = _get_serializer()
        token = s.dumps(user.email, salt="password-reset")
        reset_url = url_for("auth.reset_password", token=token, _external=True)
        msg = Message(
            subject="Redefinição de senha — Sala de Triagem",
            recipients=[user.email],
            html=(
                f"<p>Olá, {user.display_name}!</p>"
                f"<p>Clique no link abaixo para redefinir sua senha:</p>"
                f"<p><a href='{reset_url}'>{reset_url}</a></p>"
                f"<p>O link expira em 1 hora.</p>"
                f"<hr><p><small>Este NÃO é um sistema oficial.</small></p>"
            ),
        )
        mail.send(msg)
    except Exception:
        logger.exception("Failed to send password reset email to %s", user.email)
