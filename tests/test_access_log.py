"""Tests for AccessLog model and audit trail endpoint."""
import pytest
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser, DashboardSession, IntakeLink, AccessLog
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA
from app.store import submission_store, Submission
from datetime import datetime, timezone


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


@pytest.fixture()
def logged_in_client(app, client):
    """A test client with a logged-in police officer and one active session."""
    with app.app_context():
        user = PoliceUser(
            email="officer@test.com",
            display_name="Officer Test",
            is_active=True,
        )
        user.set_password("senha1234")
        _db.session.add(user)
        _db.session.commit()

        sess = DashboardSession(
            user_id=user.id,
            label="Test Shift",
            expires_at=DashboardSession.make_expires_at(),
        )
        _db.session.add(sess)
        _db.session.commit()

        link = IntakeLink(dashboard_id=sess.id, form_schema=DEFAULT_FORM_SCHEMA)
        _db.session.add(link)
        _db.session.commit()

        user_id = user.id
        session_id = sess.id

    client.post(
        "/login",
        data={"email": "officer@test.com", "password": "senha1234"},
    )

    return client, user_id, session_id


def test_access_log_model_exists(app):
    """AccessLog table must be created."""
    with app.app_context():
        assert AccessLog.__tablename__ == "access_logs"
        count = AccessLog.query.count()
        assert count == 0


def test_view_submission_creates_access_log(app, logged_in_client):
    """GET /api/sessions/<id>/submissions/<sid> must create an AccessLog entry."""
    client, user_id, session_id = logged_in_client

    # Add a submission to the in-memory store
    sub = Submission(
        submission_id="test-sub-001",
        dashboard_id=session_id,
        guest_name="João Silva",
        dob=None,
        rg=None,
        cpf=None,
        phone=None,
        address=None,
        answers={},
        narrative="",
        crime_type="outros",
        photos=[],
        received_at=datetime.now(timezone.utc),
    )
    submission_store.add(sub)

    resp = client.get(f"/api/sessions/{session_id}/submissions/test-sub-001")
    assert resp.status_code == 200

    with app.app_context():
        log = AccessLog.query.filter_by(
            user_id=user_id, submission_id="test-sub-001", action="view"
        ).first()
        assert log is not None
        assert log.ip_address is not None

    submission_store.delete("test-sub-001")


def test_my_audit_log_endpoint(app, logged_in_client):
    """GET /dashboard/my-audit-log must return 200 and show the officer's logs."""
    client, user_id, session_id = logged_in_client

    # Create a log entry directly
    with app.app_context():
        entry = AccessLog(
            user_id=user_id,
            submission_id="test-sub-002",
            action="view",
            ip_address="127.0.0.1",
            user_agent="pytest",
        )
        _db.session.add(entry)
        _db.session.commit()

    resp = client.get("/dashboard/my-audit-log")
    assert resp.status_code == 200
    assert b"Hist" in resp.data  # "Histórico"
