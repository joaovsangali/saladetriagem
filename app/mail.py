import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app

logger = logging.getLogger(__name__)


def send_confirmation_email(to_email: str, confirm_url: str) -> None:
    """Send an email confirmation link to the new user.

    If SMTP_HOST is not configured and the app is in debug mode, the link is
    printed to the console instead of sent via email.
    """
    cfg = current_app.config
    smtp_host = cfg.get("SMTP_HOST", "")

    if not smtp_host:
        if current_app.debug:
            print(f"[DEV] Confirmation link for {to_email}: {confirm_url}")
            logger.debug("Confirmation link printed to console (SMTP not configured).")
        else:
            logger.error(
                "SMTP_HOST is not configured. Cannot send confirmation email."
            )
        return

    mail_from = cfg.get("MAIL_FROM") or cfg.get("SMTP_USER", "")
    subject = "Confirme seu cadastro — Sala de Triagem"
    body_html = f"""\
<p>Olá,</p>
<p>Clique no link abaixo para confirmar seu e-mail e ativar sua conta:</p>
<p><a href="{confirm_url}">{confirm_url}</a></p>
<p>O link expira em 24 horas.</p>
<p>Se você não solicitou este cadastro, ignore este e-mail.</p>
"""
    body_text = (
        f"Acesse o link para confirmar seu e-mail:\n{confirm_url}\n\n"
        "O link expira em 24 horas."
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = mail_from
    msg["To"] = to_email
    msg.attach(MIMEText(body_text, "plain", "utf-8"))
    msg.attach(MIMEText(body_html, "html", "utf-8"))

    try:
        if cfg.get("SMTP_USE_TLS", True):
            server = smtplib.SMTP(smtp_host, cfg.get("SMTP_PORT", 587))
            server.ehlo()
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_host, cfg.get("SMTP_PORT", 587))
            server.ehlo()

        smtp_user = cfg.get("SMTP_USER", "")
        smtp_password = cfg.get("SMTP_PASSWORD", "")
        if smtp_user and smtp_password:
            server.login(smtp_user, smtp_password)

        server.sendmail(mail_from, [to_email], msg.as_string())
        server.quit()
        logger.info("Confirmation email sent to %s", to_email)
    except Exception:
        logger.exception("Failed to send confirmation email.")
