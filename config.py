import os
import logging
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
        SQLALCHEMY_ENGINE_OPTIONS["max_overflow"] = int(os.environ.get("DB_MAX_OVERFLOW", 10))
        SQLALCHEMY_ENGINE_OPTIONS["pool_recycle"] = int(os.environ.get("DB_POOL_RECYCLE", 3600))
        SQLALCHEMY_ENGINE_OPTIONS["pool_timeout"] = int(os.environ.get("DB_POOL_TIMEOUT", 30))
        # Optional SSL mode — set DATABASE_SSLMODE=require for managed databases
        # (e.g. AWS RDS, Azure Database for PostgreSQL). Defaults to "prefer"
        # which works for both SSL-enabled and plain connections.
        _sslmode = os.environ.get("DATABASE_SSLMODE", "prefer")
        if _sslmode != "disable":
            connect_args = SQLALCHEMY_ENGINE_OPTIONS.get("connect_args", {})
            connect_args["sslmode"] = _sslmode
            SQLALCHEMY_ENGINE_OPTIONS["connect_args"] = connect_args

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
    REDIS_URL = os.environ.get("REDIS_URL", "")
    RATELIMIT_STORAGE_URI = REDIS_URL or "memory://"
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
        """Validate production configuration on app startup."""
        secret = app.config.get("SECRET_KEY", "")
        if secret == _DEFAULT_SECRET_KEY or len(secret) < 32:
            raise ValueError(
                "ERRO CRÍTICO: SECRET_KEY inválida para produção.\n"
                "Gere uma chave segura com:\n"
                "  python -c \"import secrets; print(secrets.token_urlsafe(64))\"\n"
                "Configure via environment variable SECRET_KEY"
            )

        # Require S3 in production
        storage_backend = app.config.get("STORAGE_BACKEND", "")
        if storage_backend != "s3":
            raise ValueError(
                "ERRO CRÍTICO: STORAGE_BACKEND deve ser 's3' em produção.\n"
                "Configure S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY.\n"
                "Para desenvolvimento local, use Config (não ProductionConfig)."
            )

        # Require FORCE_HTTPS in production
        force_https = app.config.get("FORCE_HTTPS", False)
        if not force_https:
            raise ValueError(
                "ERRO CRÍTICO: FORCE_HTTPS deve ser True em produção.\n"
                "A aplicação está configurada para rodar atrás de proxy reverso com TLS.\n"
                "Configure FORCE_HTTPS=True no .env"
            )

        # Validate S3 credentials are set
        s3_bucket = app.config.get("S3_BUCKET", "")
        s3_access_key = app.config.get("S3_ACCESS_KEY", "")
        s3_secret_key = app.config.get("S3_SECRET_KEY", "")

        if not all([s3_bucket, s3_access_key, s3_secret_key]):
            raise ValueError(
                "ERRO CRÍTICO: Credenciais S3 incompletas.\n"
                "Configure: S3_BUCKET, S3_ACCESS_KEY, S3_SECRET_KEY"
            )

        logger = logging.getLogger(__name__)
        logger.info("ProductionConfig validated successfully")
        logger.info("Storage: S3 (bucket=%s)", s3_bucket)
        logger.info("HTTPS: forced=%s", force_https)