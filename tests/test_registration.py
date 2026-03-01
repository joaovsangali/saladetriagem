"""Minimal tests for the self-registration / double opt-in feature."""
import pytest
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser
from itsdangerous import URLSafeTimedSerializer


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
    DASHBOARD_MAX_AGE_HOURS = 24
    DEFAULT_MAX_PHOTOS = 3
    DEFAULT_MAX_PHOTO_SIZE_MB = 3


@pytest.fixture()
def app():
    application = create_app(TestConfig)
    application.config["TESTING"] = True
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _make_token(app, email):
    s = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    return s.dumps(email, salt="email-confirm")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_register_creates_inactive_user(client, app):
    """User created via /register should be is_active=False (pending confirmation)."""
    resp = client.post(
        "/register",
        data={
            "display_name": "Test User",
            "phone": "11999999999",
            "email": "test@example.com",
            "password": "senha1234",
            "password_confirm": "senha1234",
            "terms": "on",
        },
        follow_redirects=False,
    )
    # Should redirect to login after submission
    assert resp.status_code in (302, 200)

    with app.app_context():
        user = PoliceUser.query.filter_by(email="test@example.com").first()
        assert user is not None, "User was not created"
        assert user.is_active is False, "User should be inactive until confirmed"


def test_confirm_valid_token_activates_user(client, app):
    """Clicking a valid confirmation link sets is_active=True."""
    with app.app_context():
        user = PoliceUser(
            email="confirm@example.com",
            display_name="Confirm User",
            is_active=False,
        )
        user.set_password("senha1234")
        _db.session.add(user)
        _db.session.commit()

    token = _make_token(app, "confirm@example.com")
    resp = client.get(f"/confirm/{token}")
    assert resp.status_code == 200

    with app.app_context():
        user = PoliceUser.query.filter_by(email="confirm@example.com").first()
        assert user.is_active is True, "User should be active after confirmation"


def test_login_blocked_for_pending_user(client, app):
    """Login should fail when user is_active=False."""
    with app.app_context():
        user = PoliceUser(
            email="pending@example.com",
            display_name="Pending User",
            is_active=False,
        )
        user.set_password("senha1234")
        _db.session.add(user)
        _db.session.commit()

    resp = client.post(
        "/login",
        data={"email": "pending@example.com", "password": "senha1234"},
        follow_redirects=False,
    )
    # Should NOT redirect to dashboard
    assert resp.status_code != 302 or b"dashboard" not in (resp.location or b"")

    with app.app_context():
        from flask_login import current_user
        # User must remain inactive
        user = PoliceUser.query.filter_by(email="pending@example.com").first()
        assert user.is_active is False


def test_login_works_for_confirmed_user(client, app):
    """Login should succeed when user is_active=True."""
    with app.app_context():
        user = PoliceUser(
            email="active@example.com",
            display_name="Active User",
            is_active=True,
        )
        user.set_password("senha1234")
        _db.session.add(user)
        _db.session.commit()

    resp = client.post(
        "/login",
        data={"email": "active@example.com", "password": "senha1234"},
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert "dashboard" in (resp.location or "")


def test_register_no_smtp_flashes_confirm_link(client, app):
    """When SMTP is not configured, the confirmation link should appear in the flash message."""
    resp = client.post(
        "/register",
        data={
            "display_name": "No SMTP User",
            "phone": "11888888888",
            "email": "nosmtp@example.com",
            "password": "senha1234",
            "password_confirm": "senha1234",
            "terms": "on",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    # The confirmation link should be rendered on the page
    assert b"/confirm/" in resp.data
