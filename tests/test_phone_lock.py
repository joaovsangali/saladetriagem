"""Tests for phone lock after confirmation."""
import pytest
from datetime import datetime, timezone
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser


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
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _make_user(email, display_name, phone=None, phone_verified_at=None, password="senha1234"):
    user = PoliceUser(
        email=email,
        display_name=display_name,
        is_active=True,
        plan_type="premium",
        phone=phone,
        phone_verified_at=phone_verified_at,
    )
    user.set_password(password)
    _db.session.add(user)
    _db.session.commit()
    return user


def _login(client, email, password="senha1234"):
    return client.post("/login", data={"email": email, "password": password})


def test_phone_editable_before_confirmation(app, client):
    """Phone can be updated before verification."""
    with app.app_context():
        _make_user("unverified@test.com", "Unverified", phone="11111111111")

    _login(client, "unverified@test.com")
    resp = client.post(
        "/account/update-phone",
        data={"phone": "22222222222"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        user = PoliceUser.query.filter_by(email="unverified@test.com").first()
        assert user.phone == "22222222222"


def test_phone_locked_after_confirmation(app, client):
    """Phone cannot be changed after verification."""
    with app.app_context():
        _make_user(
            "verified@test.com",
            "Verified",
            phone="33333333333",
            phone_verified_at=datetime.now(timezone.utc),
        )

    _login(client, "verified@test.com")
    resp = client.post(
        "/account/update-phone",
        data={"phone": "44444444444"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        user = PoliceUser.query.filter_by(email="verified@test.com").first()
        # Phone must remain unchanged
        assert user.phone == "33333333333"


def test_phone_update_requires_login(app, client):
    """Unauthenticated request is redirected to login."""
    resp = client.post(
        "/account/update-phone",
        data={"phone": "55555555555"},
        follow_redirects=False,
    )
    assert resp.status_code in (302, 401)


def test_phone_update_too_short(app, client):
    """Phone shorter than 10 digits is rejected."""
    with app.app_context():
        _make_user("short@test.com", "Short", phone="111")

    _login(client, "short@test.com")
    resp = client.post(
        "/account/update-phone",
        data={"phone": "123"},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        user = PoliceUser.query.filter_by(email="short@test.com").first()
        assert user.phone == "111"


def test_account_page_shows_phone_readonly_when_confirmed(app, client):
    """Account page shows phone as read-only text when confirmed."""
    with app.app_context():
        _make_user(
            "conf@test.com",
            "Conf",
            phone="99999999999",
            phone_verified_at=datetime.now(timezone.utc),
        )

    _login(client, "conf@test.com")
    resp = client.get("/account/")
    assert resp.status_code == 200
    assert b"Verificado" in resp.data
    assert b"update-phone" not in resp.data


def test_account_page_shows_phone_form_when_unconfirmed(app, client):
    """Account page shows phone edit form when not yet confirmed."""
    with app.app_context():
        _make_user("unconf@test.com", "Unconf", phone="88888888888")

    _login(client, "unconf@test.com")
    resp = client.get("/account/")
    assert resp.status_code == 200
    assert b"update-phone" in resp.data
