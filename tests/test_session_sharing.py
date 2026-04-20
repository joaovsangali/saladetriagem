"""Tests for session sharing / collaboration feature."""
import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser, DashboardSession, IntakeLink, SessionCollaborator
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


def _make_session(user_id, join_code=None, active=True):
    sess = DashboardSession(
        user_id=user_id,
        label="Test Shift",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        is_active=active,
        join_code=join_code,
    )
    _db.session.add(sess)
    _db.session.commit()
    return sess


def _login(client, email, password="senha1234"):
    return client.post("/login", data={"email": email, "password": password})


# ---------------------------------------------------------------------------


def test_session_collaborator_model_exists(app):
    """SessionCollaborator table must be created."""
    with app.app_context():
        assert SessionCollaborator.__tablename__ == "session_collaborators"
        assert SessionCollaborator.query.count() == 0


def test_dashboard_session_has_join_code_field(app):
    """DashboardSession must have a join_code column."""
    with app.app_context():
        owner = _make_user("owner@test.com", "Owner", plan_type="premium")
        sess = _make_session(owner.id, join_code="ABC123")
        fetched = DashboardSession.query.get(sess.id)
        assert fetched.join_code == "ABC123"


def test_premium_user_can_join_session(app, client):
    """Premium user pode entrar em sessão com join_code válido."""
    with app.app_context():
        owner = _make_user("owner2@test.com", "Owner", plan_type="premium")
        collab_user = _make_user("collab@test.com", "Collab", plan_type="premium")
        sess = _make_session(owner.id, join_code="XYZ789")
        sess_id = sess.id
        collab_id = collab_user.id

    _login(client, "collab@test.com")
    response = client.post(
        "/dashboard/sessions/join",
        data={"join_code": "XYZ789"},
        follow_redirects=False,
    )
    # Should redirect to session_detail
    assert response.status_code == 302

    with app.app_context():
        collab = SessionCollaborator.query.filter_by(
            session_id=sess_id,
            user_id=collab_id,
        ).first()
        assert collab is not None


def test_free_user_blocked_from_joining(app, client):
    """Free user é bloqueado ao tentar entrar em sessão compartilhada."""
    with app.app_context():
        owner = _make_user("owner3@test.com", "Owner", plan_type="premium")
        free_user = _make_user("free@test.com", "Free User", plan_type="free")
        _make_session(owner.id, join_code="FREE00")

    _login(client, "free@test.com")
    response = client.post(
        "/dashboard/sessions/join",
        data={"join_code": "FREE00"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    location = response.headers.get("Location", "")
    assert "plans" in location.lower()


def test_collaborator_can_view_submissions(app, client):
    """Colaborador pode listar submissões de sessão compartilhada."""
    with app.app_context():
        owner = _make_user("owner4@test.com", "Owner", plan_type="premium")
        collab_user = _make_user("collab2@test.com", "Collab2", plan_type="premium")
        sess = _make_session(owner.id)
        sess_id = sess.id

        # Add collaborator
        collab_entry = SessionCollaborator(
            session_id=sess.id,
            user_id=collab_user.id,
        )
        _db.session.add(collab_entry)
        _db.session.commit()

    # Add a submission to the in-memory store
    sub = Submission(
        submission_id="test-share-001",
        dashboard_id=sess_id,
        guest_name="Test Person",
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

    _login(client, "collab2@test.com")
    response = client.get(f"/api/sessions/{sess_id}/submissions")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 1

    submission_store.delete("test-share-001")


def test_collaborator_cannot_close_session(app, client):
    """Colaborador NÃO pode fechar sessão (owner only)."""
    with app.app_context():
        owner = _make_user("owner5@test.com", "Owner", plan_type="premium")
        collab_user = _make_user("collab3@test.com", "Collab3", plan_type="premium")
        sess = _make_session(owner.id)
        sess_id = sess.id

        collab_entry = SessionCollaborator(
            session_id=sess.id,
            user_id=collab_user.id,
        )
        _db.session.add(collab_entry)
        _db.session.commit()

    _login(client, "collab3@test.com")
    response = client.post(f"/dashboard/sessions/{sess_id}/close")
    assert response.status_code == 404  # filter_by owner returns 404


def test_owner_can_generate_join_code(app, client):
    """Owner pode gerar um join_code para sua sessão."""
    with app.app_context():
        owner = _make_user("owner6@test.com", "Owner6", plan_type="premium")
        sess = _make_session(owner.id)
        sess_id = sess.id

    _login(client, "owner6@test.com")
    response = client.post(f"/dashboard/sessions/{sess_id}/generate-code")
    assert response.status_code == 200
    data = response.get_json()
    assert "join_code" in data
    assert len(data["join_code"]) == 6


def test_owner_can_remove_collaborator(app, client):
    """Owner pode remover colaborador da sessão."""
    with app.app_context():
        owner = _make_user("owner7@test.com", "Owner7", plan_type="premium")
        collab_user = _make_user("collab4@test.com", "Collab4", plan_type="premium")
        sess = _make_session(owner.id)
        sess_id = sess.id
        collab_uid = collab_user.id

        collab_entry = SessionCollaborator(
            session_id=sess.id,
            user_id=collab_user.id,
        )
        _db.session.add(collab_entry)
        _db.session.commit()
        collab_id = collab_entry.id

    _login(client, "owner7@test.com")
    response = client.delete(
        f"/dashboard/sessions/{sess_id}/collaborators/{collab_uid}"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "removed"

    with app.app_context():
        assert SessionCollaborator.query.get(collab_id) is None


def test_collaborator_can_assign_submission(app, client):
    """Colaborador pode marcar submissão como em atendimento."""
    with app.app_context():
        owner = _make_user("owner8@test.com", "Owner8", plan_type="premium")
        collab_user = _make_user("collab5@test.com", "Collab5", plan_type="premium")
        sess = _make_session(owner.id)
        sess_id = sess.id

        collab_entry = SessionCollaborator(
            session_id=sess.id,
            user_id=collab_user.id,
        )
        _db.session.add(collab_entry)
        _db.session.commit()

    sub = Submission(
        submission_id="test-assign-001",
        dashboard_id=sess_id,
        guest_name="Person A",
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

    _login(client, "collab5@test.com")
    response = client.post(
        f"/api/sessions/{sess_id}/submissions/test-assign-001/assign"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "assigned"
    assert data["assigned_to_name"] == "Collab5"

    submission_store.delete("test-assign-001")
