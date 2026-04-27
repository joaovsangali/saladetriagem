"""Tests for CSV export functionality."""
import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser, DashboardSession, MinimalLogEntry, IntakeLink
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA
from app.utils.csv_helpers import sanitize_csv_value, generate_csv_response


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


# ---------------------------------------------------------------------------
# Sanitizer unit tests
# ---------------------------------------------------------------------------

def test_sanitize_csv_value_normal():
    assert sanitize_csv_value("Hello") == "Hello"


def test_sanitize_csv_value_none():
    assert sanitize_csv_value(None) == ""


def test_sanitize_csv_value_empty():
    assert sanitize_csv_value("") == ""


def test_sanitize_csv_value_equals_injection():
    assert sanitize_csv_value("=SUM(A1:A10)").startswith("'")


def test_sanitize_csv_value_plus_injection():
    assert sanitize_csv_value("+cmd|' /C calc'!A0").startswith("'")


def test_sanitize_csv_value_minus_injection():
    assert sanitize_csv_value("-2+3+cmd|' /C calc'!A0").startswith("'")


def test_sanitize_csv_value_at_injection():
    assert sanitize_csv_value("@SUM(1+1)*cmd|' /C calc'!A0").startswith("'")


def test_sanitize_csv_value_tab_injection():
    assert sanitize_csv_value("\tinjection").startswith("'")


def test_sanitize_csv_value_int():
    assert sanitize_csv_value(42) == "42"


# ---------------------------------------------------------------------------
# Route: export_session_csv
# ---------------------------------------------------------------------------

def test_export_session_csv_owner(app, client):
    """Session owner can download CSV."""
    with app.app_context():
        user = _make_user("owner@csv.com", "Owner")
        sess = DashboardSession(
            user_id=user.id,
            label="CSV Test",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=False,
        )
        _db.session.add(sess)
        _db.session.commit()

        log = MinimalLogEntry(
            dashboard_id=sess.id,
            police_user_id=user.id,
            guest_display_name="Alice",
            crime_type="roubo",
            received_at=datetime.now(timezone.utc),
            closed_at=datetime.now(timezone.utc),
            status="closed",
        )
        _db.session.add(log)
        _db.session.commit()
        sess_id = sess.id

    _login(client, "owner@csv.com")
    resp = client.get(f"/dashboard/sessions/{sess_id}/export-all-csv")
    assert resp.status_code == 200
    assert b"Alice" in resp.data
    assert b"roubo" in resp.data
    assert resp.content_type.startswith("text/csv")


def test_export_session_csv_non_owner(app, client):
    """Non-owner gets 403."""
    with app.app_context():
        owner = _make_user("owner2@csv.com", "Owner2")
        other = _make_user("other2@csv.com", "Other2")
        sess = DashboardSession(
            user_id=owner.id,
            label="Not Mine",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=False,
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id

    _login(client, "other2@csv.com")
    resp = client.get(f"/dashboard/sessions/{sess_id}/export-all-csv")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Route: export_submission_csv (log entry)
# ---------------------------------------------------------------------------

def test_export_submission_csv_log_entry(app, client):
    """Can download CSV for a specific log entry."""
    with app.app_context():
        user = _make_user("owner3@csv.com", "Owner3")
        sess = DashboardSession(
            user_id=user.id,
            label="Sub CSV",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=False,
        )
        _db.session.add(sess)
        _db.session.commit()

        log = MinimalLogEntry(
            dashboard_id=sess.id,
            police_user_id=user.id,
            guest_display_name="Bob",
            crime_type="furto",
            received_at=datetime.now(timezone.utc),
            closed_at=datetime.now(timezone.utc),
            status="closed",
        )
        _db.session.add(log)
        _db.session.commit()
        sess_id = sess.id
        log_id = log.id

    _login(client, "owner3@csv.com")
    resp = client.get(f"/dashboard/sessions/{sess_id}/submissions/{log_id}/csv")
    assert resp.status_code == 200
    assert b"Bob" in resp.data
    assert resp.content_type.startswith("text/csv")


def test_export_submission_csv_non_owner(app, client):
    """Non-owner gets 403."""
    with app.app_context():
        owner = _make_user("owner4@csv.com", "Owner4")
        other = _make_user("other4@csv.com", "Other4")
        sess = DashboardSession(
            user_id=owner.id,
            label="Not Mine",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=False,
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id

    _login(client, "other4@csv.com")
    resp = client.get(f"/dashboard/sessions/{sess_id}/submissions/1/csv")
    assert resp.status_code == 403


def test_export_submission_csv_not_found(app, client):
    """Returns 404 for non-existent log entry."""
    with app.app_context():
        user = _make_user("owner5@csv.com", "Owner5")
        sess = DashboardSession(
            user_id=user.id,
            label="Empty",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=False,
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id

    _login(client, "owner5@csv.com")
    resp = client.get(f"/dashboard/sessions/{sess_id}/submissions/9999/csv")
    assert resp.status_code == 404


def test_csv_header_present(app, client):
    """CSV export includes expected column headers."""
    with app.app_context():
        user = _make_user("owner6@csv.com", "Owner6")
        sess = DashboardSession(
            user_id=user.id,
            label="Headers",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=False,
        )
        _db.session.add(sess)
        _db.session.commit()

        log = MinimalLogEntry(
            dashboard_id=sess.id,
            police_user_id=user.id,
            guest_display_name="Carol",
            crime_type="roubo",
            received_at=datetime.now(timezone.utc),
            status="received",
        )
        _db.session.add(log)
        _db.session.commit()
        sess_id = sess.id

    _login(client, "owner6@csv.com")
    resp = client.get(f"/dashboard/sessions/{sess_id}/export-all-csv")
    assert resp.status_code == 200
    content = resp.data.decode("utf-8")
    assert "Nome" in content
    assert "Tipo" in content
    assert "Status" in content
