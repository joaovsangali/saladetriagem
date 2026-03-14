"""Tests for HTTPS redirect middleware and security headers."""
import pytest
from app import create_app


class _TestConfig:
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
    FORCE_HTTPS = False


class _ForceHTTPSConfig(_TestConfig):
    FORCE_HTTPS = True


@pytest.fixture()
def client_no_https():
    app = create_app(_TestConfig)
    return app.test_client()


@pytest.fixture()
def client_force_https():
    app = create_app(_ForceHTTPSConfig)
    return app.test_client()


# ---------------------------------------------------------------------------
# HTTPS redirect tests
# ---------------------------------------------------------------------------

def test_no_redirect_when_force_https_false(client_no_https):
    """When FORCE_HTTPS=False, plain HTTP requests are not redirected."""
    resp = client_no_https.get("/login")
    assert resp.status_code != 301


def test_http_redirected_to_https_when_force_https_true(client_force_https):
    """When FORCE_HTTPS=True and X-Forwarded-Proto is http, a 301 is returned."""
    resp = client_force_https.get(
        "/login",
        headers={"X-Forwarded-Proto": "http"},
    )
    assert resp.status_code == 301
    assert resp.location.startswith("https://")


def test_https_request_not_redirected(client_force_https):
    """When FORCE_HTTPS=True but request already uses HTTPS, no redirect."""
    resp = client_force_https.get(
        "/login",
        headers={"X-Forwarded-Proto": "https"},
    )
    assert resp.status_code != 301


# ---------------------------------------------------------------------------
# Security headers tests
# ---------------------------------------------------------------------------

def test_security_headers_present(client_no_https):
    """Standard security headers must be present on all responses."""
    resp = client_no_https.get("/login")
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("Referrer-Policy") == "no-referrer"
    assert "Strict-Transport-Security" in resp.headers
