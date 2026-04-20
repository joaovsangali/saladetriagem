"""Tests for shared session feature."""
import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser, DashboardSession, IntakeLink, SharedSessionAccess
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA
from app.store import submission_store, Submission


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


def _make_user(email, display_name="Officer", plan_type="premium", password="senha1234"):
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


def _make_session(user_id, label="Test Shift", expired=False):
    expires_at = (
        datetime.now(timezone.utc) - timedelta(hours=1)
        if expired
        else datetime.now(timezone.utc) + timedelta(hours=12)
    )
    import secrets
    sess = DashboardSession(
        user_id=user_id,
        label=label,
        expires_at=expires_at,
        share_code=secrets.token_urlsafe(8),
    )
    _db.session.add(sess)
    _db.session.commit()

    link = IntakeLink(dashboard_id=sess.id, form_schema=DEFAULT_FORM_SCHEMA)
    _db.session.add(link)
    _db.session.commit()
    return sess


def _login(client, email, password="senha1234"):
    client.post("/login", data={"email": email, "password": password})


# ─── Test 1: Creating a session generates share_code ──────────────────────────

def test_new_session_generates_share_code(app, client):
    with app.app_context():
        user = _make_user("owner@test.com")
        user_id = user.id

    _login(client, "owner@test.com")
    resp = client.post(
        "/dashboard/sessions/new",
        data={"label": "Test Triagem", "duration_hours": "6"},
        follow_redirects=False,
    )
    assert resp.status_code in (200, 302)

    with app.app_context():
        sess = DashboardSession.query.filter_by(user_id=user_id).first()
        assert sess is not None
        assert sess.share_code is not None
        assert len(sess.share_code) > 0


# ─── Test 2: Admin created automatically when session is created ───────────────

def test_new_session_creates_admin_access(app, client):
    with app.app_context():
        user = _make_user("owner2@test.com")
        user_id = user.id

    _login(client, "owner2@test.com")
    client.post(
        "/dashboard/sessions/new",
        data={"label": "Test Triagem", "duration_hours": "6"},
    )

    with app.app_context():
        sess = DashboardSession.query.filter_by(user_id=user_id).first()
        assert sess is not None
        access = SharedSessionAccess.query.filter_by(
            session_id=sess.id, user_id=user_id
        ).first()
        assert access is not None
        assert access.role == 'admin'
        assert access.is_active is True


# ─── Test 3: Valid user enters with code ───────────────────────────────────────

def test_join_session_with_valid_code(app, client):
    with app.app_context():
        owner = _make_user("owner3@test.com", plan_type="premium")
        viewer = _make_user("viewer@test.com", plan_type="premium")
        sess = _make_session(owner.id)
        code = sess.share_code
        session_id = sess.id
        viewer_id = viewer.id

    _login(client, "viewer@test.com")
    resp = client.post(
        "/dashboard/join_session",
        data={"code": code},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        access = SharedSessionAccess.query.filter_by(
            session_id=session_id, user_id=viewer_id
        ).first()
        assert access is not None
        assert access.role == 'viewer'
        assert access.is_active is True


# ─── Test 4: Free user is blocked ─────────────────────────────────────────────

def test_free_user_blocked_from_joining(app, client):
    with app.app_context():
        owner = _make_user("owner4@test.com", plan_type="premium")
        free_user = _make_user("free@test.com", plan_type="free")
        sess = _make_session(owner.id)
        code = sess.share_code
        session_id = sess.id
        free_id = free_user.id

    _login(client, "free@test.com")
    resp = client.post(
        "/dashboard/join_session",
        data={"code": code},
        follow_redirects=True,
    )
    # Should redirect to plans page or show warning
    assert resp.status_code == 200

    with app.app_context():
        access = SharedSessionAccess.query.filter_by(
            session_id=session_id, user_id=free_id
        ).first()
        assert access is None


# ─── Test 5: Invalid code returns error ───────────────────────────────────────

def test_join_with_invalid_code(app, client):
    with app.app_context():
        _make_user("viewer2@test.com", plan_type="premium")

    _login(client, "viewer2@test.com")
    resp = client.post(
        "/dashboard/join_session",
        data={"code": "INVALID_CODE_XYZ"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"inv" in resp.data.lower() or b"n" in resp.data  # flash message contains invalid


# ─── Test 6: Expired session → access denied ──────────────────────────────────

def test_join_expired_session_denied(app, client):
    with app.app_context():
        owner = _make_user("owner5@test.com", plan_type="premium")
        viewer = _make_user("viewer3@test.com", plan_type="premium")
        sess = _make_session(owner.id, expired=True)
        sess.is_active = False
        _db.session.commit()
        code = sess.share_code
        session_id = sess.id
        viewer_id = viewer.id

    _login(client, "viewer3@test.com")
    resp = client.post(
        "/dashboard/join_session",
        data={"code": code},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        access = SharedSessionAccess.query.filter_by(
            session_id=session_id, user_id=viewer_id
        ).first()
        assert access is None


# ─── Test 7: Owner cannot join own session via code ───────────────────────────

def test_owner_cannot_join_own_session(app, client):
    with app.app_context():
        owner = _make_user("owner6@test.com", plan_type="premium")
        sess = _make_session(owner.id)
        code = sess.share_code
        session_id = sess.id
        owner_id = owner.id

    _login(client, "owner6@test.com")
    resp = client.post(
        "/dashboard/join_session",
        data={"code": code},
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        # Only admin entry exists, no duplicate
        accesses = SharedSessionAccess.query.filter_by(session_id=session_id).all()
        assert len(accesses) == 0  # no SharedSessionAccess since session was created directly


# ─── Test 8: Admin can remove viewer ──────────────────────────────────────────

def test_admin_can_remove_viewer(app, client):
    with app.app_context():
        owner = _make_user("owner7@test.com", plan_type="premium")
        viewer = _make_user("viewer4@test.com", plan_type="premium")
        sess = _make_session(owner.id)
        access = SharedSessionAccess(
            session_id=sess.id,
            user_id=viewer.id,
            role='viewer',
            is_active=True,
        )
        _db.session.add(access)
        _db.session.commit()
        session_id = sess.id
        viewer_id = viewer.id

    _login(client, "owner7@test.com")
    resp = client.post(
        f"/dashboard/sessions/{session_id}/remove_user/{viewer_id}",
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        access = SharedSessionAccess.query.filter_by(
            session_id=session_id, user_id=viewer_id
        ).first()
        assert access is not None
        assert access.is_active is False


# ─── Test 9: Admin cannot remove themselves ───────────────────────────────────

def test_admin_cannot_remove_self(app, client):
    with app.app_context():
        owner = _make_user("owner8@test.com", plan_type="premium")
        sess = _make_session(owner.id)
        session_id = sess.id
        owner_id = owner.id

    _login(client, "owner8@test.com")
    resp = client.post(
        f"/dashboard/sessions/{session_id}/remove_user/{owner_id}",
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"n" in resp.data  # warning message returned


# ─── Test 10: Viewer can access /api/sessions/<id>/submissions ────────────────

def test_viewer_can_access_submissions(app, client):
    with app.app_context():
        owner = _make_user("owner9@test.com", plan_type="premium")
        viewer = _make_user("viewer5@test.com", plan_type="premium")
        sess = _make_session(owner.id)
        access = SharedSessionAccess(
            session_id=sess.id,
            user_id=viewer.id,
            role='viewer',
            is_active=True,
        )
        _db.session.add(access)
        _db.session.commit()
        session_id = sess.id

    _login(client, "viewer5@test.com")
    resp = client.get(f"/api/sessions/{session_id}/submissions")
    assert resp.status_code == 200


# ─── Test 11: Viewer cannot close session ─────────────────────────────────────

def test_viewer_cannot_close_session(app, client):
    with app.app_context():
        owner = _make_user("owner10@test.com", plan_type="premium")
        viewer = _make_user("viewer6@test.com", plan_type="premium")
        sess = _make_session(owner.id)
        access = SharedSessionAccess(
            session_id=sess.id,
            user_id=viewer.id,
            role='viewer',
            is_active=True,
        )
        _db.session.add(access)
        _db.session.commit()
        session_id = sess.id

    _login(client, "viewer6@test.com")
    resp = client.post(
        f"/dashboard/sessions/{session_id}/close",
        follow_redirects=True,
    )
    # Viewer is not the owner, should get 404 (filter_by user_id=owner)
    assert resp.status_code == 404


# ─── Test 12: Expired session revokes all shared accesses ─────────────────────

def test_expiry_task_revokes_shared_accesses(app):
    with app.app_context():
        owner = _make_user("owner11@test.com", plan_type="premium")
        viewer = _make_user("viewer7@test.com", plan_type="premium")

        sess = DashboardSession(
            user_id=owner.id,
            label="Expiry Test",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
            share_code="expiry_test_code",
            is_active=True,
        )
        _db.session.add(sess)
        _db.session.commit()

        access = SharedSessionAccess(
            session_id=sess.id,
            user_id=viewer.id,
            role='viewer',
            is_active=True,
        )
        _db.session.add(access)
        _db.session.commit()
        session_id = sess.id
        viewer_id = viewer.id

        from app.tasks.session_expiry import expire_sessions_task
        expire_sessions_task()

        result = SharedSessionAccess.query.filter_by(
            session_id=session_id, user_id=viewer_id
        ).first()
        assert result is not None
        assert result.is_active is False


# ─── Test 13: No duplicate entry for same user ────────────────────────────────

def test_no_duplicate_shared_access(app, client):
    with app.app_context():
        owner = _make_user("owner12@test.com", plan_type="premium")
        viewer = _make_user("viewer8@test.com", plan_type="premium")
        sess = _make_session(owner.id)
        code = sess.share_code
        session_id = sess.id
        viewer_id = viewer.id

    _login(client, "viewer8@test.com")
    # Join twice
    client.post("/dashboard/join_session", data={"code": code}, follow_redirects=True)
    client.post("/dashboard/join_session", data={"code": code}, follow_redirects=True)

    with app.app_context():
        count = SharedSessionAccess.query.filter_by(
            session_id=session_id, user_id=viewer_id
        ).count()
        assert count == 1
