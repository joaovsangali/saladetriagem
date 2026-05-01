"""Tests for plan rules: session duration, upload limits, and custom attachments."""
import json
import io
import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db as _db
from app.models import (
    PoliceUser, DashboardSession, IntakeLink, CustomIntakeTemplate
)
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


_VALID_SCHEMA = {
    "fields": [
        {"id": "name", "label": "Nome", "type": "text", "required": True},
        {"id": "email", "label": "E-mail", "type": "email", "required": True},
    ]
}


# ---------------------------------------------------------------------------
# Plan limits unit tests
# ---------------------------------------------------------------------------

def test_free_plan_duration_is_6h():
    from app.plans import PLANS
    assert PLANS['free']['max_session_duration_hours'] == 6


def test_premium_plan_duration_is_12h():
    from app.plans import PLANS
    assert PLANS['premium']['max_session_duration_hours'] == 12


def test_enterprise_plan_duration_is_24h():
    from app.plans import PLANS
    assert PLANS['enterprise']['max_session_duration_hours'] == 24


def test_free_plan_uploads_is_0():
    from app.plans import PLANS
    assert PLANS['free']['max_uploads_per_submission'] == 0


def test_premium_plan_uploads_is_3():
    from app.plans import PLANS
    assert PLANS['premium']['max_uploads_per_submission'] == 3


def test_enterprise_plan_uploads_is_6():
    from app.plans import PLANS
    assert PLANS['enterprise']['max_uploads_per_submission'] == 6


# ---------------------------------------------------------------------------
# plan_helpers tests
# ---------------------------------------------------------------------------

def test_can_use_infinite_sessions_enterprise_custom(app):
    with app.app_context():
        user = _make_user("ent@test.com", "Ent", plan_type="enterprise")
        from app.utils.plan_helpers import can_use_infinite_sessions
        assert can_use_infinite_sessions(user, "custom") is True


def test_cannot_use_infinite_sessions_enterprise_police(app):
    with app.app_context():
        user = _make_user("ent2@test.com", "Ent2", plan_type="enterprise")
        from app.utils.plan_helpers import can_use_infinite_sessions
        assert can_use_infinite_sessions(user, "police") is False


def test_cannot_use_infinite_sessions_premium(app):
    with app.app_context():
        user = _make_user("prem@test.com", "Prem", plan_type="premium")
        from app.utils.plan_helpers import can_use_infinite_sessions
        assert can_use_infinite_sessions(user, "custom") is False


def test_cannot_use_infinite_sessions_free(app):
    with app.app_context():
        user = _make_user("free@test.com", "Free", plan_type="free")
        from app.utils.plan_helpers import can_use_infinite_sessions
        assert can_use_infinite_sessions(user, "custom") is False


def test_get_max_uploads_premium(app):
    with app.app_context():
        user = _make_user("prem2@test.com", "Prem2", plan_type="premium")
        from app.utils.plan_helpers import get_max_uploads
        assert get_max_uploads(user) == 3


def test_get_max_uploads_enterprise(app):
    with app.app_context():
        user = _make_user("ent3@test.com", "Ent3", plan_type="enterprise")
        from app.utils.plan_helpers import get_max_uploads
        assert get_max_uploads(user) == 6


def test_get_max_session_duration_free(app):
    with app.app_context():
        user = _make_user("free2@test.com", "Free2", plan_type="free")
        from app.utils.plan_helpers import get_max_session_duration
        assert get_max_session_duration(user) == 6


def test_can_attach_files_false_by_default():
    from app.utils.plan_helpers import can_attach_files
    assert can_attach_files({"fields": []}) is False


def test_can_attach_files_true_when_set():
    from app.utils.plan_helpers import can_attach_files
    assert can_attach_files({"fields": [], "allow_attachments": True}) is True


def test_can_attach_files_false_for_none_schema():
    from app.utils.plan_helpers import can_attach_files
    assert can_attach_files(None) is False


# ---------------------------------------------------------------------------
# is_expired model tests
# ---------------------------------------------------------------------------

def test_infinite_session_never_expires(app):
    with app.app_context():
        user = _make_user("ent4@test.com", "Ent4", plan_type="enterprise")
        sess = DashboardSession(
            user_id=user.id,
            label="Infinite",
            expires_at=None,
            is_infinite=True,
        )
        _db.session.add(sess)
        _db.session.commit()
        assert sess.is_expired is False


def test_regular_expired_session(app):
    with app.app_context():
        user = _make_user("prem3@test.com", "Prem3", plan_type="premium")
        sess = DashboardSession(
            user_id=user.id,
            label="Expired",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        _db.session.add(sess)
        _db.session.commit()
        assert sess.is_expired is True


def test_session_with_none_expires_not_expired(app):
    """Session with expires_at=None and is_infinite=False should not expire (safeguard)."""
    with app.app_context():
        user = _make_user("prem4@test.com", "Prem4", plan_type="premium")
        sess = DashboardSession(
            user_id=user.id,
            label="NoExpiry",
            expires_at=None,
            is_infinite=False,
        )
        _db.session.add(sess)
        _db.session.commit()
        assert sess.is_expired is False


# ---------------------------------------------------------------------------
# Session creation: duration limits
# ---------------------------------------------------------------------------

def test_free_user_cannot_create_session_over_6h(app, client):
    with app.app_context():
        _make_user("free3@test.com", "Free3", plan_type="free")
    _login(client, "free3@test.com")
    resp = client.post(
        "/dashboard/sessions/new",
        data={
            "label": "Test",
            "duration_hours": "8",  # exceeds free plan limit of 6h
            "intake_type": "police",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    # Session should NOT have been created
    with app.app_context():
        assert DashboardSession.query.filter_by(label="Test").first() is None


def test_enterprise_can_create_infinite_custom_session(app, client):
    with app.app_context():
        user = _make_user("ent5@test.com", "Ent5", plan_type="enterprise")
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="Custom Tpl", schema=_VALID_SCHEMA
        )
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "ent5@test.com")
    resp = client.post(
        "/dashboard/sessions/new",
        data={
            "label": "Infinite Session",
            "intake_type": "custom",
            "custom_template_id": str(tpl_id),
            "is_infinite": "true",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        sess = DashboardSession.query.filter_by(label="Infinite Session").first()
        assert sess is not None
        assert sess.is_infinite is True
        assert sess.expires_at is None


def test_enterprise_cannot_create_infinite_police_session(app, client):
    """Enterprise user with police intake cannot create infinite session."""
    with app.app_context():
        _make_user("ent6@test.com", "Ent6", plan_type="enterprise")

    _login(client, "ent6@test.com")
    resp = client.post(
        "/dashboard/sessions/new",
        data={
            "label": "Police Infinite Attempt",
            "duration_hours": "12",
            "intake_type": "police",
            "is_infinite": "true",  # should be ignored for police
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        sess = DashboardSession.query.filter_by(label="Police Infinite Attempt").first()
        assert sess is not None
        assert sess.is_infinite is False
        assert sess.expires_at is not None


def test_premium_cannot_create_infinite_session(app, client):
    """Premium user with custom intake cannot create infinite session."""
    with app.app_context():
        user = _make_user("prem5@test.com", "Prem5", plan_type="premium")
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="Custom Tpl", schema=_VALID_SCHEMA
        )
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "prem5@test.com")
    resp = client.post(
        "/dashboard/sessions/new",
        data={
            "label": "Premium Custom Session",
            "duration_hours": "6",
            "intake_type": "custom",
            "custom_template_id": str(tpl_id),
            "is_infinite": "true",  # should be blocked for premium
        },
        follow_redirects=True,
    )
    # premium can't use custom templates at all
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Upload limits: police intake
# ---------------------------------------------------------------------------

def _make_session_with_link(user, plan_type="premium"):
    sess = DashboardSession(
        user_id=user.id,
        label="Test Session",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
    )
    _db.session.add(sess)
    _db.session.commit()
    link = IntakeLink(dashboard_id=sess.id, form_schema=DEFAULT_FORM_SCHEMA)
    _db.session.add(link)
    _db.session.commit()
    return sess, link


def _make_fake_image():
    """Create a minimal JPEG-like bytes for testing."""
    return b'\xff\xd8\xff\xe0' + b'\x00' * 100  # fake JPEG bytes


def test_premium_blocked_at_4_uploads(app, client):
    with app.app_context():
        user = _make_user("prem6@test.com", "Prem6", plan_type="premium")
        sess, link = _make_session_with_link(user)
        token = link.token

    # Try submitting with 4 files (premium limit is 3)
    resp = client.post(
        f"/t/{token}/submit",
        data={
            "guest_name": "Test User",
            "crime_type": "outros",
            "photos": [
                (io.BytesIO(_make_fake_image()), "photo1.jpg"),
                (io.BytesIO(_make_fake_image()), "photo2.jpg"),
                (io.BytesIO(_make_fake_image()), "photo3.jpg"),
                (io.BytesIO(_make_fake_image()), "photo4.jpg"),
            ],
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    # Should redirect back to the form, NOT to /ok
    assert resp.status_code == 302
    assert "/ok" not in resp.location


def test_enterprise_accepts_6_uploads(app, client):
    with app.app_context():
        user = _make_user("ent7@test.com", "Ent7", plan_type="enterprise")
        sess, link = _make_session_with_link(user, plan_type="enterprise")
        token = link.token

    # Try submitting with 6 files (enterprise limit is 6)
    resp = client.post(
        f"/t/{token}/submit",
        data={
            "guest_name": "Test User",
            "crime_type": "outros",
            "photos": [
                (io.BytesIO(_make_fake_image()), f"photo{i}.jpg")
                for i in range(6)
            ],
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    # Should redirect to /ok (success)
    assert resp.status_code == 302
    assert "/ok" in resp.location


def test_enterprise_blocked_at_7_uploads(app, client):
    with app.app_context():
        user = _make_user("ent8@test.com", "Ent8", plan_type="enterprise")
        sess, link = _make_session_with_link(user, plan_type="enterprise")
        token = link.token

    # Try submitting with 7 files (enterprise limit is 6)
    resp = client.post(
        f"/t/{token}/submit",
        data={
            "guest_name": "Test User",
            "crime_type": "outros",
            "photos": [
                (io.BytesIO(_make_fake_image()), f"photo{i}.jpg")
                for i in range(7)
            ],
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    # Should redirect back to the form, NOT to /ok
    assert resp.status_code == 302
    assert "/ok" not in resp.location


# ---------------------------------------------------------------------------
# Custom attachments: allow_attachments flag
# ---------------------------------------------------------------------------

def _make_custom_session_with_link(user, allow_attachments=False):
    schema = dict(_VALID_SCHEMA)
    schema['allow_attachments'] = allow_attachments
    tpl = CustomIntakeTemplate(
        user_id=user.id,
        name="Custom",
        schema=schema,
    )
    _db.session.add(tpl)
    _db.session.commit()

    sess = DashboardSession(
        user_id=user.id,
        label="Custom Session",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        intake_type="custom",
        custom_template_id=tpl.id,
    )
    _db.session.add(sess)
    _db.session.commit()

    link = IntakeLink(dashboard_id=sess.id, form_schema=DEFAULT_FORM_SCHEMA)
    _db.session.add(link)
    _db.session.commit()
    return sess, link


def test_custom_without_attachments_rejects_files(app, client):
    with app.app_context():
        user = _make_user("ent9@test.com", "Ent9", plan_type="enterprise")
        sess, link = _make_custom_session_with_link(user, allow_attachments=False)
        token = link.token

    resp = client.post(
        f"/t/{token}/submit",
        data={
            "field_name": "João da Silva",
            "field_email": "joao@test.com",
            "photos": [(io.BytesIO(_make_fake_image()), "photo.jpg")],
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    # Should redirect back to form, NOT to /ok
    assert resp.status_code == 302
    assert "/ok" not in resp.location


def test_custom_with_attachments_accepts_files(app, client):
    with app.app_context():
        user = _make_user("ent10@test.com", "Ent10", plan_type="enterprise")
        sess, link = _make_custom_session_with_link(user, allow_attachments=True)
        token = link.token

    resp = client.post(
        f"/t/{token}/submit",
        data={
            "field_name": "Unique Test Name Plan Rules",
            "field_email": "uniqueplanrules@test.com",
            "photos": [(io.BytesIO(_make_fake_image()), "photo.jpg")],
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    # Should succeed and redirect to /ok
    assert resp.status_code == 302
    assert "/ok" in resp.location


def test_custom_with_attachments_enforces_upload_limit(app, client):
    """Premium user with custom form + allow_attachments: max 3 files."""
    with app.app_context():
        user = _make_user("prem7@test.com", "Prem7", plan_type="premium")
        schema = dict(_VALID_SCHEMA)
        schema['allow_attachments'] = True
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="Custom", schema=schema,
        )
        _db.session.add(tpl)
        _db.session.commit()
        sess = DashboardSession(
            user_id=user.id,
            label="Custom Session",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
            intake_type="custom",
            custom_template_id=tpl.id,
        )
        _db.session.add(sess)
        _db.session.commit()
        link = IntakeLink(dashboard_id=sess.id, form_schema=DEFAULT_FORM_SCHEMA)
        _db.session.add(link)
        _db.session.commit()
        token = link.token

    # Try 4 files (premium limit is 3)
    resp = client.post(
        f"/t/{token}/submit",
        data={
            "field_name": "Test User",
            "field_email": "test@test.com",
            "photos": [
                (io.BytesIO(_make_fake_image()), f"photo{i}.jpg")
                for i in range(4)
            ],
        },
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    # Should redirect back to form, NOT to /ok
    assert resp.status_code == 302
    assert "/ok" not in resp.location


# ---------------------------------------------------------------------------
# allow_attachments in template creation
# ---------------------------------------------------------------------------

def test_create_template_with_allow_attachments(app, client):
    with app.app_context():
        _make_user("ent11@test.com", "Ent11", plan_type="enterprise")

    _login(client, "ent11@test.com")
    resp = client.post(
        "/dashboard/custom-templates/create",
        data={
            "name": "Template With Attachments",
            "schema_json": json.dumps(_VALID_SCHEMA),
            "allow_attachments": "true",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        tpl = CustomIntakeTemplate.query.filter_by(name="Template With Attachments").first()
        assert tpl is not None
        assert tpl.schema.get('allow_attachments') is True


def test_create_template_without_allow_attachments(app, client):
    with app.app_context():
        _make_user("ent12@test.com", "Ent12", plan_type="enterprise")

    _login(client, "ent12@test.com")
    resp = client.post(
        "/dashboard/custom-templates/create",
        data={
            "name": "Template Without Attachments",
            "schema_json": json.dumps(_VALID_SCHEMA),
            # no allow_attachments field
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        tpl = CustomIntakeTemplate.query.filter_by(name="Template Without Attachments").first()
        assert tpl is not None
        assert tpl.schema.get('allow_attachments') is False


# ---------------------------------------------------------------------------
# Number field backend validation
# ---------------------------------------------------------------------------

def _make_custom_session_with_number_field(user):
    """Create a custom session with a number field and return the intake token."""
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text", "required": True},
            {"id": "quantidade", "label": "Quantidade", "type": "number", "required": True},
        ]
    }
    tpl = CustomIntakeTemplate(user_id=user.id, name="NumTest", schema=schema)
    _db.session.add(tpl)
    _db.session.commit()
    sess = DashboardSession(
        user_id=user.id,
        label="Num Session",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        intake_type="custom",
        custom_template_id=tpl.id,
    )
    _db.session.add(sess)
    _db.session.commit()
    link = IntakeLink(dashboard_id=sess.id, form_schema=DEFAULT_FORM_SCHEMA)
    _db.session.add(link)
    _db.session.commit()
    return link.token


def test_number_field_negative_value_rejected(app, client):
    """Custom form: negative number values must be rejected."""
    with app.app_context():
        user = _make_user("num1@test.com", "Num1", plan_type="enterprise")
        token = _make_custom_session_with_number_field(user)

    resp = client.post(
        f"/t/{token}/submit",
        data={"field_name": "NegativeTest NumField1", "field_quantidade": "-5"},
        follow_redirects=False,
    )
    # Should redirect back to the form, NOT to /ok
    assert resp.status_code == 302
    assert "/ok" not in resp.location


def test_number_field_valid_value_accepted(app, client):
    """Custom form: valid non-negative number values must be accepted."""
    with app.app_context():
        user = _make_user("num2@test.com", "Num2", plan_type="enterprise")
        token = _make_custom_session_with_number_field(user)

    resp = client.post(
        f"/t/{token}/submit",
        data={"field_name": "ValidTest NumField2", "field_quantidade": "42"},
        follow_redirects=False,
    )
    # Should redirect to /ok (success)
    assert resp.status_code == 302
    assert "/ok" in resp.location


def test_number_field_zero_accepted(app, client):
    """Custom form: zero is a valid number value."""
    with app.app_context():
        user = _make_user("num3@test.com", "Num3", plan_type="enterprise")
        token = _make_custom_session_with_number_field(user)

    resp = client.post(
        f"/t/{token}/submit",
        data={"field_name": "ZeroTest NumField3", "field_quantidade": "0"},
        follow_redirects=False,
    )
    # 0 is a valid value (non-negative), should succeed
    assert resp.status_code == 302
    assert "/ok" in resp.location


def test_number_field_non_numeric_rejected(app, client):
    """Custom form: non-numeric values in number fields must be rejected."""
    with app.app_context():
        user = _make_user("num4@test.com", "Num4", plan_type="enterprise")
        token = _make_custom_session_with_number_field(user)

    resp = client.post(
        f"/t/{token}/submit",
        data={"field_name": "InvalidTest NumField4", "field_quantidade": "abc"},
        follow_redirects=False,
    )
    # Should redirect back to form (invalid)
    assert resp.status_code == 302
    assert "/ok" not in resp.location


# ---------------------------------------------------------------------------
# Celery expiry: infinite sessions skipped
# ---------------------------------------------------------------------------

def test_infinite_session_skipped_by_expiry_task(app):
    with app.app_context():
        user = _make_user("ent13@test.com", "Ent13", plan_type="enterprise")
        sess = DashboardSession(
            user_id=user.id,
            label="Infinite",
            expires_at=None,
            is_infinite=True,
            is_active=True,
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id

        from app.tasks.session_expiry import expire_sessions_task
        expire_sessions_task()

        sess = _db.session.get(DashboardSession, sess_id)
        assert sess.is_active is True  # still active, not expired


def test_expired_session_expired_by_task(app):
    with app.app_context():
        user = _make_user("prem8@test.com", "Prem8", plan_type="premium")
        sess = DashboardSession(
            user_id=user.id,
            label="Expired",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_infinite=False,
            is_active=True,
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id

        from app.tasks.session_expiry import expire_sessions_task
        expire_sessions_task()

        sess = _db.session.get(DashboardSession, sess_id)
        assert sess.is_active is False  # expired by task


# ---------------------------------------------------------------------------
# Plan limits: new values
# ---------------------------------------------------------------------------

def test_free_plan_sessions_per_month_is_10():
    from app.plans import PLANS
    assert PLANS['free']['max_sessions_per_month'] == 10


def test_free_plan_submissions_per_session_is_15():
    from app.plans import PLANS
    assert PLANS['free']['max_submissions_per_session'] == 15


def test_premium_plan_submissions_per_session_is_50():
    from app.plans import PLANS
    assert PLANS['premium']['max_submissions_per_session'] == 50


def test_enterprise_sessions_per_month_is_unlimited():
    from app.plans import PLANS
    assert PLANS['enterprise']['max_sessions_per_month'] is None


def test_enterprise_submissions_per_session_is_unlimited():
    from app.plans import PLANS
    assert PLANS['enterprise']['max_submissions_per_session'] is None


def test_free_max_active_sessions_is_1():
    from app.plans import PLANS
    assert PLANS['free']['max_active_sessions'] == 1


def test_premium_max_active_sessions_is_1():
    from app.plans import PLANS
    assert PLANS['premium']['max_active_sessions'] == 1


def test_enterprise_max_active_sessions_is_3():
    from app.plans import PLANS
    assert PLANS['enterprise']['max_active_sessions'] == 3


# ---------------------------------------------------------------------------
# Delete last session: no 500 error
# ---------------------------------------------------------------------------

def test_delete_last_session_succeeds(app, client):
    """Deleting the only session must succeed and redirect to dashboard."""
    with app.app_context():
        user = _make_user("del1@test.com", "Del1", plan_type="free")
        sess = DashboardSession(
            user_id=user.id,
            label="Only Session",
            is_active=False,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        _db.session.add(sess)
        _db.session.commit()
        sess_id = sess.id

    _login(client, "del1@test.com")
    resp = client.post(
        f"/dashboard/sessions/{sess_id}/delete",
        follow_redirects=False,
    )
    # Must redirect (302), not 500
    assert resp.status_code == 302
    assert "/dashboard" in resp.location or resp.location == "/"

    with app.app_context():
        assert DashboardSession.query.filter_by(id=sess_id).first() is None


def test_delete_shared_session_with_collaborators_succeeds(app, client):
    """Deleting a session that has SessionCollaborator records must succeed."""
    from app.models import SessionCollaborator
    with app.app_context():
        owner = _make_user("del2@test.com", "Del2", plan_type="enterprise")
        collaborator = _make_user("collab@test.com", "Collab", plan_type="premium")
        sess = DashboardSession(
            user_id=owner.id,
            label="Shared Session",
            is_active=False,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        _db.session.add(sess)
        _db.session.commit()
        sc = SessionCollaborator(session_id=sess.id, user_id=collaborator.id)
        _db.session.add(sc)
        _db.session.commit()
        sess_id = sess.id

    _login(client, "del2@test.com")
    resp = client.post(
        f"/dashboard/sessions/{sess_id}/delete",
        follow_redirects=False,
    )
    # Must redirect (302), not 500
    assert resp.status_code == 302

    with app.app_context():
        assert DashboardSession.query.filter_by(id=sess_id).first() is None
        assert SessionCollaborator.query.filter_by(session_id=sess_id).count() == 0


def test_delete_all_closed_sessions_succeeds(app, client):
    """Deleting all closed sessions (including the last one) must succeed."""
    with app.app_context():
        user = _make_user("del3@test.com", "Del3", plan_type="premium")
        user_id = user.id
        for i in range(2):
            sess = DashboardSession(
                user_id=user.id,
                label=f"Session {i}",
                is_active=False,
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            )
            _db.session.add(sess)
        _db.session.commit()

    _login(client, "del3@test.com")
    resp = client.post(
        "/dashboard/sessions/delete-closed",
        follow_redirects=False,
    )
    # Must redirect (302), not 500
    assert resp.status_code == 302

    with app.app_context():
        assert DashboardSession.query.filter_by(user_id=user_id).count() == 0


def test_enterprise_allows_3_active_sessions(app, client):
    """Enterprise users can create up to 3 active sessions."""
    from app.models import CustomIntakeTemplate
    with app.app_context():
        user = _make_user("ent_act@test.com", "EntAct", plan_type="enterprise")

    _login(client, "ent_act@test.com")

    # Create 3 sessions
    for i in range(3):
        resp = client.post(
            "/dashboard/sessions/new",
            data={
                "label": f"Active Session {i+1}",
                "duration_hours": "6",
                "intake_type": "police",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200

    with app.app_context():
        from app.models import PoliceUser
        u = PoliceUser.query.filter_by(email="ent_act@test.com").first()
        active_count = DashboardSession.query.filter_by(
            user_id=u.id, is_active=True
        ).count()
        assert active_count == 3


def test_enterprise_blocked_at_4th_active_session(app, client):
    """Enterprise users cannot create a 4th active session."""
    with app.app_context():
        user = _make_user("ent_act2@test.com", "EntAct2", plan_type="enterprise")
        # Pre-create 3 active sessions directly
        for i in range(3):
            sess = DashboardSession(
                user_id=user.id,
                label=f"Pre Session {i+1}",
                is_active=True,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            )
            _db.session.add(sess)
        _db.session.commit()

    _login(client, "ent_act2@test.com")
    resp = client.post(
        "/dashboard/sessions/new",
        data={
            "label": "4th Session",
            "duration_hours": "6",
            "intake_type": "police",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert DashboardSession.query.filter_by(label="4th Session").first() is None
