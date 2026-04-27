"""Tests for custom template edit feature."""
import json
import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser, CustomIntakeTemplate


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


def _make_user(email, display_name, plan_type="enterprise", password="senha1234"):
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

_UPDATED_SCHEMA = {
    "fields": [
        {"id": "name", "label": "Nome", "type": "text", "required": True},
        {"id": "email", "label": "E-mail", "type": "email", "required": True},
        {"id": "phone", "label": "Telefone", "type": "text", "required": False},
    ]
}


def test_edit_template_get(app, client):
    """GET /edit renders the edit form with existing data."""
    with app.app_context():
        user = _make_user("owner@test.com", "Owner")
        tpl = CustomIntakeTemplate(user_id=user.id, name="Orig", schema=_VALID_SCHEMA)
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "owner@test.com")
    resp = client.get(f"/dashboard/custom-templates/{tpl_id}/edit")
    assert resp.status_code == 200
    assert b"Orig" in resp.data


def test_owner_can_edit_template(app, client):
    """Owner can update template name and schema."""
    with app.app_context():
        user = _make_user("owner2@test.com", "Owner2")
        tpl = CustomIntakeTemplate(user_id=user.id, name="OldName", schema=_VALID_SCHEMA)
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "owner2@test.com")
    resp = client.post(
        f"/dashboard/custom-templates/{tpl_id}/edit",
        data={
            "name": "NewName",
            "schema_json": json.dumps(_UPDATED_SCHEMA),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"NewName" in resp.data

    with app.app_context():
        tpl = CustomIntakeTemplate.query.get(tpl_id)
        assert tpl.name == "NewName"
        assert len(tpl.schema["fields"]) == 3


def test_non_owner_cannot_edit(app, client):
    """Another user receives 404 when trying to edit someone else's template."""
    with app.app_context():
        owner = _make_user("own3@test.com", "Own3")
        other = _make_user("other3@test.com", "Other3")
        tpl = CustomIntakeTemplate(user_id=owner.id, name="Mine", schema=_VALID_SCHEMA)
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "other3@test.com")
    resp = client.get(f"/dashboard/custom-templates/{tpl_id}/edit")
    assert resp.status_code == 404


def test_edit_template_invalid_schema(app, client):
    """Posting an invalid schema returns an error without saving."""
    with app.app_context():
        user = _make_user("owner4@test.com", "Owner4")
        tpl = CustomIntakeTemplate(user_id=user.id, name="Keep", schema=_VALID_SCHEMA)
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "owner4@test.com")
    bad_schema = {"fields": [{"id": "x", "label": "X", "type": "text"}]}  # only 1 field
    resp = client.post(
        f"/dashboard/custom-templates/{tpl_id}/edit",
        data={
            "name": "Keep",
            "schema_json": json.dumps(bad_schema),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"inv" in resp.data.lower()

    with app.app_context():
        tpl = CustomIntakeTemplate.query.get(tpl_id)
        assert tpl.name == "Keep"
        assert len(tpl.schema["fields"]) == 2


def test_edit_template_non_enterprise_blocked(app, client):
    """Non-Enterprise user is redirected away from edit page."""
    with app.app_context():
        user = _make_user("free5@test.com", "Free5", plan_type="free")
        # Create template directly (bypassing plan check)
        tpl = CustomIntakeTemplate(user_id=user.id, name="T", schema=_VALID_SCHEMA)
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "free5@test.com")
    resp = client.get(f"/dashboard/custom-templates/{tpl_id}/edit", follow_redirects=True)
    assert b"Enterprise" in resp.data


def test_edit_template_allow_attachments_flag(app, client):
    """allow_attachments flag is correctly saved in schema."""
    with app.app_context():
        user = _make_user("owner6@test.com", "Owner6")
        tpl = CustomIntakeTemplate(user_id=user.id, name="Attach", schema=_VALID_SCHEMA)
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "owner6@test.com")
    resp = client.post(
        f"/dashboard/custom-templates/{tpl_id}/edit",
        data={
            "name": "Attach",
            "schema_json": json.dumps(_VALID_SCHEMA),
            "allow_attachments": "true",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        tpl = CustomIntakeTemplate.query.get(tpl_id)
        assert tpl.schema.get("allow_attachments") is True
