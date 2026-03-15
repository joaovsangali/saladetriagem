import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

_DEFAULT_SECRET_KEY = "dev-secret-change-in-prod"


def _bool_env(name: str, default: str = "False") -> bool:
    return os.environ.get(name, default).lower() in ("true", "1", "yes")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", _DEFAULT_SECRET_KEY)

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'triagem.db')}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Connection pool settings only apply to PostgreSQL (SQLite ignores these
    # options and raises an error if passed explicitly via engine options).
    _db_url = SQLALCHEMY_DATABASE_URI
    SQLALCHEMY_ENGINE_OPTIONS: dict = {"pool_pre_ping": True}
    if _db_url.startswith("postgresql"):
        SQLALCHEMY_ENGINE_OPTIONS["pool_size"] = int(os.environ.get("DB_POOL_SIZE", 10))
        SQLALCHEMY_ENGINE_OPTIONS["max_overflow"] = int(os.environ.get("DB_MAX_OVERFLOW", 20))

    # ------------------------------------------------------------------
    # WTForms / CSRF
    # ------------------------------------------------------------------
    WTF_CSRF_ENABLED = True

    # ------------------------------------------------------------------
    # File uploads
    # ------------------------------------------------------------------
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024  # 12 MB
    DASHBOARD_MAX_AGE_HOURS = 12
    DEFAULT_MAX_PHOTOS = 3
    DEFAULT_MAX_PHOTO_SIZE_MB = 3

    # ------------------------------------------------------------------
    # Rate limiting
    # ------------------------------------------------------------------
    # Use Redis when available, fall back to memory
    REDIS_URL = os.environ.get("REDIS_URL", "")
    RATELIMIT_STORAGE_URI = (
        os.environ.get("REDIS_URL", "") or "memory://"
    )
    RATELIMIT_DEFAULT = "200 per day;50 per hour"

    # ------------------------------------------------------------------
    # Celery
    # ------------------------------------------------------------------
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "")
    CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "")

    # ------------------------------------------------------------------
    # Object storage
    # ------------------------------------------------------------------
    STORAGE_BACKEND = os.environ.get("STORAGE_BACKEND", "local")  # "local" | "s3"
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    S3_BUCKET = os.environ.get("S3_BUCKET", "")
    S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "")
    S3_REGION = os.environ.get("S3_REGION", "us-east-1")
    S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
    S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")
    S3_SIGNED_URL_TTL = int(os.environ.get("S3_SIGNED_URL_TTL", 3600))

    # ------------------------------------------------------------------
    # E-mail
    # ------------------------------------------------------------------
    SMTP_HOST = os.environ.get("SMTP_HOST", "")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_USE_TLS = _bool_env("SMTP_USE_TLS", "True")
    MAIL_FROM = os.environ.get("MAIL_FROM", "")
    CONFIRMATION_TOKEN_MAX_AGE = 86400  # 24 hours in seconds

    # ------------------------------------------------------------------
    # Misc security
    # ------------------------------------------------------------------
    REQUIRE_CPF_FOR_SIGNUP = _bool_env("REQUIRE_CPF_FOR_SIGNUP", "False")
    FORCE_HTTPS = _bool_env("FORCE_HTTPS", "False")


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
