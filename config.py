import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

_DEFAULT_SECRET_KEY = "dev-secret-change-in-prod"


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", _DEFAULT_SECRET_KEY)
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'triagem.db')}")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = True
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024  # 12MB
    DASHBOARD_MAX_AGE_HOURS = 12
    DEFAULT_MAX_PHOTOS = 3
    DEFAULT_MAX_PHOTO_SIZE_MB = 3
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_DEFAULT = "200 per day;50 per hour"
    REQUIRE_CPF_FOR_SIGNUP = os.environ.get("REQUIRE_CPF_FOR_SIGNUP", "False").lower() in ("true", "1", "yes")
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "True").lower() in ("true", "1", "yes")
    MAIL_FROM = os.environ.get("MAIL_FROM", "")
    CONFIRMATION_TOKEN_MAX_AGE = 86400  # 24 hours in seconds
    FORCE_HTTPS = os.environ.get("FORCE_HTTPS", "False").lower() in ("true", "1", "yes")


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)

    @classmethod
    def init_app(cls, app):
        secret = app.config.get("SECRET_KEY", "")
        if secret == _DEFAULT_SECRET_KEY or len(secret) < 32:
            raise ValueError(
                "ERRO CRÍTICO: SECRET_KEY inválida para produção.\n"
                "Gere uma chave segura com:\n"
                "  python -c \"import secrets; print(secrets.token_urlsafe(64))\"\n"
                "Configure via environment variable SECRET_KEY"
            )
