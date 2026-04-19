"""Tests for SessionCollaborator model and session sharing functionality."""
import pytest
from datetime import datetime, timedelta, timezone
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser, DashboardSession, IntakeLink, SessionCollaborator
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret-key-12345678"
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
    """
    Create the app and tables once.  Yield the app WITHOUT an active context so
    that each test-client request gets its own fresh application context (and
    therefore a fresh `flask.g`, which Flask-Login uses to store current_user).
    This prevents cross-request user contamination.
    """
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
    yield application
    with application.app_context():
        _db.session.remove()
        _db.drop_all()


def _make_user(app, email, display_name, plan_type="premium"):
    """Create a user inside a fresh app context."""
    with app.app_context():
        user = PoliceUser(
            email=email,
            display_name=display_name,
            is_active=True,
            plan_type=plan_type,
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        user.set_password("senha1234")
        _db.session.add(user)
        _db.session.commit()
        return user.id


def _make_session(app, user_id, label="Test Session"):
    """Create a dashboard session inside a fresh app context."""
    with app.app_context():
        sess = DashboardSession(
            user_id=user_id,
            label=label,
            expires_at=DashboardSession.make_expires_at(),
        )
        _db.session.add(sess)
        _db.session.commit()
        link = IntakeLink(dashboard_id=sess.id, form_schema=DEFAULT_FORM_SCHEMA)
        _db.session.add(link)
        _db.session.commit()
        return sess.id


def _login(app, email):
    """Create a test client and log in as `email`; returns the client."""
    c = app.test_client()
    c.post("/login", data={"email": email, "password": "senha1234"})
    return c


def _collab_count(app, session_id):
    """Return the number of active collaborators for the given session."""
    with app.app_context():
        return SessionCollaborator.query.filter_by(
            dashboard_id=session_id, is_active=True
        ).count()


# ───── Model tests ─────────────────────────────────────────────────────────────

def test_session_collaborator_model(app):
    """SessionCollaborator table must exist and be queryable."""
    with app.app_context():
        assert SessionCollaborator.__tablename__ == "session_collaborators"
        assert SessionCollaborator.query.count() == 0


def test_dashboard_session_has_share_code(app):
    """DashboardSession must have share_code and share_code_expires_at columns."""
    owner_id = _make_user(app, "sc_owner@test.com", "SC Owner")
    session_id = _make_session(app, owner_id)
    with app.app_context():
        sess = DashboardSession.query.get(session_id)
        assert sess.share_code is None
        assert sess.share_code_expires_at is None


# ───── Share code generation ────────────────────────────────────────────────────

def test_generate_share_code_owner(app):
    """Owner can generate a share code via POST."""
    owner_id = _make_user(app, "owner1@test.com", "Owner 1")
    session_id = _make_session(app, owner_id)
    owner_c = _login(app, "owner1@test.com")

    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "share_code" in data
    code = data["share_code"]
    assert len(code) == 8

    with app.app_context():
        sess = DashboardSession.query.get(session_id)
        assert sess.share_code == code
        assert sess.share_code_expires_at is not None


def test_generate_share_code_forbidden_for_non_owner(app):
    """Non-owner cannot generate a share code."""
    owner_id = _make_user(app, "owner2@test.com", "Owner 2")
    session_id = _make_session(app, owner_id)
    _make_user(app, "collab2@test.com", "Collab 2")
    collab_c = _login(app, "collab2@test.com")

    resp = collab_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    assert resp.status_code == 403


# ───── Join session ─────────────────────────────────────────────────────────────

def test_join_session_valid_code(app):
    """Collab user can join a session with a valid share code."""
    owner_id = _make_user(app, "owner3@test.com", "Owner 3")
    session_id = _make_session(app, owner_id)
    collab_id = _make_user(app, "collab3@test.com", "Collab 3")

    owner_c = _login(app, "owner3@test.com")
    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    code = resp.get_json()["share_code"]

    collab_c = _login(app, "collab3@test.com")
    resp = collab_c.post("/dashboard/sessions/join", data={"share_code": code})
    assert resp.status_code in (200, 302)

    with app.app_context():
        collab = SessionCollaborator.query.filter_by(
            dashboard_id=session_id, user_id=collab_id
        ).first()
        assert collab is not None
        assert collab.is_active is True
        assert collab.access_level == "viewer"


def test_join_session_invalid_code(app):
    """Invalid code returns error and does not create collaborator."""
    _make_user(app, "collab4@test.com", "Collab 4")
    collab_c = _login(app, "collab4@test.com")

    resp = collab_c.post(
        "/dashboard/sessions/join",
        data={"share_code": "INVALID1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert SessionCollaborator.query.count() == 0


def test_join_session_expired_code(app):
    """Expired share code is rejected."""
    owner_id = _make_user(app, "owner5@test.com", "Owner 5")
    session_id = _make_session(app, owner_id)
    _make_user(app, "collab5@test.com", "Collab 5")

    owner_c = _login(app, "owner5@test.com")
    owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")

    with app.app_context():
        sess = DashboardSession.query.get(session_id)
        sess.share_code_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        code = sess.share_code
        _db.session.commit()

    collab_c = _login(app, "collab5@test.com")
    resp = collab_c.post(
        "/dashboard/sessions/join",
        data={"share_code": code},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert SessionCollaborator.query.count() == 0


def test_join_own_session_redirects(app):
    """Owner cannot join their own session as collaborator."""
    owner_id = _make_user(app, "owner6@test.com", "Owner 6")
    session_id = _make_session(app, owner_id)

    owner_c = _login(app, "owner6@test.com")
    owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    with app.app_context():
        code = DashboardSession.query.get(session_id).share_code

    resp = owner_c.post(
        "/dashboard/sessions/join",
        data={"share_code": code},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert SessionCollaborator.query.count() == 0


# ───── Access control ──────────────────────────────────────────────────────────

def test_collaborator_can_view_session(app):
    """Collaborator can access session_detail after joining."""
    owner_id = _make_user(app, "owner7@test.com", "Owner 7")
    session_id = _make_session(app, owner_id)
    _make_user(app, "collab7@test.com", "Collab 7")

    owner_c = _login(app, "owner7@test.com")
    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    code = resp.get_json()["share_code"]

    collab_c = _login(app, "collab7@test.com")
    collab_c.post("/dashboard/sessions/join", data={"share_code": code})

    resp = collab_c.get(f"/dashboard/sessions/{session_id}")
    assert resp.status_code == 200


def test_non_collaborator_cannot_view_session(app):
    """User with no collaboration link cannot access session."""
    owner_id = _make_user(app, "owner8@test.com", "Owner 8")
    session_id = _make_session(app, owner_id)
    _make_user(app, "other8@test.com", "Other 8")

    other_c = _login(app, "other8@test.com")
    resp = other_c.get(f"/dashboard/sessions/{session_id}")
    assert resp.status_code == 403


def test_viewer_cannot_close_session(app):
    """Viewer role cannot close a session."""
    owner_id = _make_user(app, "owner9@test.com", "Owner 9")
    session_id = _make_session(app, owner_id)
    _make_user(app, "collab9@test.com", "Collab 9")

    owner_c = _login(app, "owner9@test.com")
    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    code = resp.get_json()["share_code"]

    collab_c = _login(app, "collab9@test.com")
    collab_c.post("/dashboard/sessions/join", data={"share_code": code})

    resp = collab_c.post(f"/dashboard/sessions/{session_id}/close")
    assert resp.status_code == 403


def test_non_owner_cannot_delete_session(app):
    """Non-owner cannot delete a closed session."""
    owner_id = _make_user(app, "owner10@test.com", "Owner 10")
    session_id = _make_session(app, owner_id)
    _make_user(app, "collab10@test.com", "Collab 10")

    owner_c = _login(app, "owner10@test.com")
    # Close session first (delete requires is_active=False)
    owner_c.post(f"/dashboard/sessions/{session_id}/close")

    collab_c = _login(app, "collab10@test.com")
    resp = collab_c.post(f"/dashboard/sessions/{session_id}/delete")
    assert resp.status_code == 403


# ───── Remove collaborator ─────────────────────────────────────────────────────

def test_owner_can_remove_collaborator(app):
    """Owner can remove an active collaborator."""
    owner_id = _make_user(app, "owner11@test.com", "Owner 11")
    session_id = _make_session(app, owner_id)
    collab_id = _make_user(app, "collab11@test.com", "Collab 11")

    owner_c = _login(app, "owner11@test.com")
    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    code = resp.get_json()["share_code"]

    collab_c = _login(app, "collab11@test.com")
    collab_c.post("/dashboard/sessions/join", data={"share_code": code})

    resp = owner_c.delete(f"/dashboard/sessions/{session_id}/collaborators/{collab_id}")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"

    with app.app_context():
        collab = SessionCollaborator.query.filter_by(
            dashboard_id=session_id, user_id=collab_id
        ).first()
        assert collab.is_active is False


def test_collaborator_cannot_remove_others(app):
    """Collaborator cannot remove owner or other collaborators."""
    owner_id = _make_user(app, "owner12@test.com", "Owner 12")
    session_id = _make_session(app, owner_id)
    _make_user(app, "collab12@test.com", "Collab 12")

    owner_c = _login(app, "owner12@test.com")
    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    code = resp.get_json()["share_code"]

    collab_c = _login(app, "collab12@test.com")
    collab_c.post("/dashboard/sessions/join", data={"share_code": code})

    # Collaborator tries to remove the owner
    resp = collab_c.delete(f"/dashboard/sessions/{session_id}/collaborators/{owner_id}")
    assert resp.status_code == 403


# ───── List collaborators ──────────────────────────────────────────────────────

def test_list_collaborators_as_owner(app):
    """Owner gets list of active collaborators."""
    owner_id = _make_user(app, "owner13@test.com", "Owner 13")
    session_id = _make_session(app, owner_id)
    collab_id = _make_user(app, "collab13@test.com", "Collab 13")

    owner_c = _login(app, "owner13@test.com")
    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    code = resp.get_json()["share_code"]

    collab_c = _login(app, "collab13@test.com")
    collab_c.post("/dashboard/sessions/join", data={"share_code": code})

    resp = owner_c.get(f"/dashboard/sessions/{session_id}/collaborators")
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["user_id"] == collab_id
    assert data[0]["display_name"] == "Collab 13"


# ───── Plan limits ─────────────────────────────────────────────────────────────

def test_collaborator_limit_enforced(app):
    """Cannot add more collaborators than the plan allows."""
    from app.plans import PLANS
    max_collabs = PLANS["free"]["max_collaborators_per_session"]

    owner_id = _make_user(app, "limit_owner@test.com", "Limit Owner", plan_type="free")
    session_id = _make_session(app, owner_id, "Limit Test")

    owner_c = _login(app, "limit_owner@test.com")
    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    code = resp.get_json()["share_code"]

    # Add collaborators up to the limit
    for i in range(max_collabs):
        _make_user(app, f"limitcollab{i}@test.com", f"LC {i}")
        c = _login(app, f"limitcollab{i}@test.com")
        c.post("/dashboard/sessions/join", data={"share_code": code})

    # One more user tries to join — should be rejected
    _make_user(app, "extra_limit@test.com", "Extra Limit")
    extra_c = _login(app, "extra_limit@test.com")
    extra_c.post(
        "/dashboard/sessions/join",
        data={"share_code": code},
        follow_redirects=True,
    )

    assert _collab_count(app, session_id) == max_collabs


# ───── Index page shared sessions ──────────────────────────────────────────────

def test_index_shows_shared_sessions(app):
    """Dashboard index page shows shared sessions section for collaborator."""
    owner_id = _make_user(app, "owner14@test.com", "Owner 14")
    session_id = _make_session(app, owner_id)
    _make_user(app, "collab14@test.com", "Collab 14")

    owner_c = _login(app, "owner14@test.com")
    resp = owner_c.post(f"/dashboard/sessions/{session_id}/share/generate")
    code = resp.get_json()["share_code"]

    collab_c = _login(app, "collab14@test.com")
    collab_c.post("/dashboard/sessions/join", data={"share_code": code})

    resp = collab_c.get("/dashboard/")
    assert resp.status_code == 200
    assert b"Triagens Compartilhadas Comigo" in resp.data
