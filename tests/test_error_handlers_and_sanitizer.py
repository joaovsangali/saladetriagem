"""Tests for custom error handlers and log sanitization."""
import logging
import pytest
from app import create_app
from app.log_sanitizer import SanitizingFilter


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key"
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


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    with application.app_context():
        from app.extensions import db
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


# ---------------------------------------------------------------------------
# Error handler tests
# ---------------------------------------------------------------------------

def test_404_returns_html_template(client):
    """Unknown HTML routes must return 404 with a template, no stacktrace."""
    resp = client.get("/rota-que-nao-existe")
    assert resp.status_code == 404
    assert b"404" in resp.data
    assert b"Traceback" not in resp.data


def test_api_404_returns_json(client):
    """Unknown /api/ routes must return JSON 404, not HTML."""
    resp = client.get("/api/rota-inexistente")
    assert resp.status_code == 404
    data = resp.get_json()
    assert data is not None
    assert "error" in data
    assert b"Traceback" not in resp.data


# ---------------------------------------------------------------------------
# Log sanitization tests
# ---------------------------------------------------------------------------

def _make_record(msg: str) -> logging.LogRecord:
    record = logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0, msg=msg,
        args=(), exc_info=None,
    )
    return record


def test_sanitizer_masks_cpf():
    f = SanitizingFilter()
    record = _make_record("CPF do cliente: 12345678901")
    f.filter(record)
    assert "12345678901" not in str(record.msg)
    assert "****" in str(record.msg)


def test_sanitizer_masks_rg():
    f = SanitizingFilter()
    record = _make_record("RG: 1234567890")
    f.filter(record)
    assert "1234567890" not in str(record.msg)


def test_sanitizer_masks_email():
    f = SanitizingFilter()
    record = _make_record("Email: fulano@example.com")
    f.filter(record)
    assert "fulano@example.com" not in str(record.msg)
    assert "@example.com" in str(record.msg)  # domain preserved partially


def test_sanitizer_masks_address():
    f = SanitizingFilter()
    record = _make_record("Endereço: Rua das Flores, 123, Centro")
    f.filter(record)
    assert "Rua das Flores" not in str(record.msg)
    assert "ENDEREÇO REMOVIDO" in str(record.msg)


def test_sanitizer_passes_normal_text():
    f = SanitizingFilter()
    record = _make_record("Usuário fez login com sucesso.")
    f.filter(record)
    assert record.msg == "Usuário fez login com sucesso."
