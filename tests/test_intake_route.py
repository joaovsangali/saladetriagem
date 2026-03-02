"""Regression tests for the public guest intake route GET /t/<token>."""
import pytest
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser, DashboardSession, IntakeLink
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA


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
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def active_link(app):
    """Create an active intake link in the database and return it."""
    with app.app_context():
        user = PoliceUser(email="cop@test.com", display_name="Officer", is_active=True)
        user.set_password("test1234")
        _db.session.add(user)
        _db.session.commit()

        session = DashboardSession(
            user_id=user.id,
            label="Test Shift",
            expires_at=DashboardSession.make_expires_at(),
        )
        _db.session.add(session)
        _db.session.commit()

        link = IntakeLink(dashboard_id=session.id, form_schema=DEFAULT_FORM_SCHEMA)
        _db.session.add(link)
        _db.session.commit()

        return link.token


def test_intake_route_is_registered(app):
    """The route GET /t/<token> must be registered in the app URL map."""
    rules = [str(rule) for rule in app.url_map.iter_rules()]
    assert "/t/<token>" in rules, "Route GET /t/<token> is not registered"


def test_intake_form_returns_200_for_valid_token(client, active_link):
    """GET /t/<token> must return 200 for an existing active token."""
    resp = client.get(f"/t/{active_link}")
    assert resp.status_code == 200, (
        f"Expected 200 for valid token, got {resp.status_code}"
    )


def test_intake_form_returns_404_for_unknown_token(client):
    """GET /t/<token> must return 404 when the token does not exist."""
    resp = client.get("/t/this-token-does-not-exist")
    assert resp.status_code == 404


def test_intake_form_url_is_generated_via_url_for(client, app, active_link):
    """The intake URL shown in the dashboard must use url_for, not a hardcoded string."""
    # Log in and create a session to verify url_for generates the correct path
    with app.app_context():
        from flask import url_for
        with app.test_request_context():
            url = url_for("intake.form", token=active_link)
    assert url == f"/t/{active_link}", (
        f"url_for('intake.form', token=...) generated unexpected path: {url}"
    )


def test_intake_submit_post_works(client, active_link):
    """POST /t/<token>/submit must process the form and redirect to /ok."""
    resp = client.post(
        f"/t/{active_link}/submit",
        data={
            "guest_name": "Test Guest",
            "crime_type": "roubo",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/t/{active_link}/ok" in resp.location
