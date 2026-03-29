"""Tests for SECRET_KEY validation and ProductionConfig."""
import pytest
from config import Config, ProductionConfig


class _GoodProdConfig(ProductionConfig):
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    RATELIMIT_DEFAULT = "10000 per day"
    SMTP_HOST = ""
    MAIL_FROM = ""
    CONFIRMATION_TOKEN_MAX_AGE = 86400
    REQUIRE_CPF_FOR_SIGNUP = False
    MAX_CONTENT_LENGTH = 12 * 1024 * 1024
    DASHBOARD_MAX_AGE_HOURS = 12
    DEFAULT_MAX_PHOTOS = 3
    DEFAULT_MAX_PHOTO_SIZE_MB = 3
    SECRET_KEY = "a" * 64  # valid key
    STORAGE_BACKEND = "s3"  # required in production
    FORCE_HTTPS = True  # required in production
    S3_BUCKET = "test-bucket"
    S3_ACCESS_KEY = "test-access-key"
    S3_SECRET_KEY = "test-secret-key"


class _DefaultKeyProdConfig(_GoodProdConfig):
    SECRET_KEY = "dev-secret-change-in-prod"


class _ShortKeyProdConfig(_GoodProdConfig):
    SECRET_KEY = "short"


def test_production_config_accepts_valid_key():
    """ProductionConfig.init_app must not raise when SECRET_KEY is valid."""
    from app import create_app

    app = create_app(_GoodProdConfig)
    assert app is not None


def test_production_config_rejects_default_key():
    """ProductionConfig.init_app must raise ValueError for the default key."""
    from app import create_app

    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app(_DefaultKeyProdConfig)


def test_production_config_rejects_short_key():
    """ProductionConfig.init_app must raise ValueError when key is shorter than 32 chars."""
    from app import create_app

    with pytest.raises(ValueError, match="SECRET_KEY"):
        create_app(_ShortKeyProdConfig)


def test_dev_config_does_not_raise_for_default_key():
    """The base Config must allow the default key (dev mode)."""
    from app import create_app

    class DevConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
        SQLALCHEMY_TRACK_MODIFICATIONS = False
        WTF_CSRF_ENABLED = False
        RATELIMIT_ENABLED = False
        RATELIMIT_STORAGE_URI = "memory://"
        RATELIMIT_DEFAULT = "10000 per day"
        SMTP_HOST = ""
        MAIL_FROM = ""
        CONFIRMATION_TOKEN_MAX_AGE = 86400
        REQUIRE_CPF_FOR_SIGNUP = False
        MAX_CONTENT_LENGTH = 12 * 1024 * 1024
        DASHBOARD_MAX_AGE_HOURS = 12
        DEFAULT_MAX_PHOTOS = 3
        DEFAULT_MAX_PHOTO_SIZE_MB = 3

    app = create_app(DevConfig)
    assert app is not None
