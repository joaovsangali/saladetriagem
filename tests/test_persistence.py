"""Tests for idempotent submission persistence."""
import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser, DashboardSession, MinimalLogEntry, IntakeLink
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


def _make_user(email, display_name, plan_type="premium", password="senha1234"):
    user = PoliceUser(
        email=email,
        display_name=display_name,
        is_active=True,
        plan_type=plan_type,
    )
    user.set_password(password)
    _db.session.add(user)
    _db.session.commit()
    return user


def _login(client, email, password="senha1234"):
    return client.post("/login", data={"email": email, "password": password})


def _make_submission(name, crime_type="roubo", received_at=None):
    """Create a mock submission object."""
    sub = MagicMock()
    sub.guest_name = name
    sub.crime_type = crime_type
    sub.received_at = received_at or datetime.now(timezone.utc)
    return sub


def test_all_submissions_persisted_on_close(app, client):
    """Closing session persists all pending submissions as MinimalLogEntry."""
    with app.app_context():
        user = _make_user("close@test.com", "Closer")
        sess = DashboardSession(
            user_id=user.id,
            label="Close Test",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id
        user_id = user.id

        link = IntakeLink(dashboard_id=sess_id, form_schema=DEFAULT_FORM_SCHEMA)
        _db.session.add(link)
        _db.session.commit()

        received_at = datetime.now(timezone.utc).replace(microsecond=0)
        sub1 = _make_submission("Alice", received_at=received_at)
        sub2 = _make_submission("Bob", received_at=received_at + timedelta(seconds=1))

        with patch("app.dashboard.routes.submission_store") as mock_store:
            mock_store.list_for_dashboard.return_value = [sub1, sub2]
            mock_store.count_for_dashboard.return_value = 2
            mock_store.purge_dashboard.return_value = None

            from app.dashboard.routes import _persist_pending_submissions
            count = _persist_pending_submissions(sess, status="received")
            _db.session.commit()

        assert count == 2
        entries = MinimalLogEntry.query.filter_by(dashboard_id=sess_id).all()
        assert len(entries) == 2
        names = {e.guest_display_name for e in entries}
        assert "Alice" in names
        assert "Bob" in names


def test_no_duplicate_entries(app):
    """Running _persist_pending_submissions twice does not create duplicates."""
    with app.app_context():
        user = _make_user("nodup@test.com", "NoDup")
        sess = DashboardSession(
            user_id=user.id,
            label="NoDup Test",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id

        received_at = datetime.now(timezone.utc).replace(microsecond=0)
        sub = _make_submission("Charlie", received_at=received_at)

        with patch("app.dashboard.routes.submission_store") as mock_store:
            mock_store.list_for_dashboard.return_value = [sub]

            from app.dashboard.routes import _persist_pending_submissions

            # First call
            count1 = _persist_pending_submissions(sess, status="received")
            _db.session.commit()

            # Second call — should detect existing entry and skip
            count2 = _persist_pending_submissions(sess, status="received")
            _db.session.commit()

        assert count1 == 1
        assert count2 == 0

        entries = MinimalLogEntry.query.filter_by(dashboard_id=sess_id).all()
        assert len(entries) == 1


def test_persist_skips_existing_entries(app):
    """If an entry already exists in DB, it is not duplicated."""
    with app.app_context():
        user = _make_user("skip@test.com", "Skip")
        sess = DashboardSession(
            user_id=user.id,
            label="Skip Test",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id

        now = datetime.now(timezone.utc).replace(microsecond=0)

        # Pre-insert entry
        entry = MinimalLogEntry(
            dashboard_id=sess_id,
            police_user_id=user.id,
            guest_display_name="Dave",
            crime_type="furto",
            received_at=now,
            closed_at=now,
            status="received",
        )
        _db.session.add(entry)
        _db.session.commit()

        sub = _make_submission("Dave", crime_type="furto", received_at=now)

        with patch("app.dashboard.routes.submission_store") as mock_store:
            mock_store.list_for_dashboard.return_value = [sub]

            from app.dashboard.routes import _persist_pending_submissions
            count = _persist_pending_submissions(sess, status="received")
            _db.session.commit()

        assert count == 0
        entries = MinimalLogEntry.query.filter_by(dashboard_id=sess_id).all()
        assert len(entries) == 1
