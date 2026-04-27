"""Tests for custom intake templates feature."""
import pytest
from datetime import datetime, timezone, timedelta
from app import create_app
from app.extensions import db as _db
from app.models import (
    PoliceUser, DashboardSession, IntakeLink, CustomIntakeTemplate
)
from app.schemas.crime_types import DEFAULT_FORM_SCHEMA
from app.utils.schema_validator import validate_custom_intake_schema


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
# Schema validator unit tests
# ---------------------------------------------------------------------------

def test_valid_schema_passes():
    valid, err = validate_custom_intake_schema(_VALID_SCHEMA)
    assert valid is True
    assert err is None


def test_schema_too_few_fields():
    schema = {"fields": [{"id": "name", "label": "Nome", "type": "text"}]}
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "2 campos" in err


def test_schema_missing_fields_key():
    valid, err = validate_custom_intake_schema({"other": []})
    assert valid is False
    assert "fields" in err


def test_schema_invalid_type():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "x", "label": "X", "type": "invalid_type"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "não permitido" in err


def test_schema_html_in_label_rejected():
    schema = {
        "fields": [
            {"id": "name", "label": "<script>alert(1)</script>", "type": "text"},
            {"id": "email", "label": "E-mail", "type": "email"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "HTML" in err


def test_schema_not_a_dict():
    valid, err = validate_custom_intake_schema("not a dict")
    assert valid is False


def test_schema_select_requires_options():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "x", "label": "Opção", "type": "select"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "opção" in err.lower()


# ---------------------------------------------------------------------------
# v2 field type unit tests
# ---------------------------------------------------------------------------

def test_schema_radio_valid():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "color", "label": "Cor", "type": "radio",
             "options": ["Vermelho", "Azul", "Verde"]},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is True, err


def test_schema_radio_requires_options():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "q", "label": "Q", "type": "radio"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "opção" in err.lower() or "uma opção" in err.lower()


def test_schema_checkbox_valid():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "items", "label": "Itens", "type": "checkbox",
             "options": ["A", "B"]},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is True, err


def test_schema_scale_valid():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "pain", "label": "Dor", "type": "scale",
             "min": 0, "max": 10, "step": 1},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is True, err


def test_schema_scale_invalid_min():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "pain", "label": "Dor", "type": "scale", "min": "bad"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "numérico" in err


def test_schema_section_header_counts_as_display_only():
    """A schema with 2 submittable fields + 1 section_header is valid."""
    schema = {
        "fields": [
            {"id": "sec1", "label": "Seção 1", "type": "section_header"},
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "email", "label": "E-mail", "type": "email"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is True, err


def test_schema_only_display_only_fields_invalid():
    """Only section_header fields → fails minimum submittable count."""
    schema = {
        "fields": [
            {"id": "h1", "label": "Header 1", "type": "section_header"},
            {"id": "h2", "label": "Header 2", "type": "section_header"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "2 campos" in err


def test_schema_image_display_valid():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "img", "label": "Foto do produto", "type": "image_display",
             "image_url": "https://example.com/img.jpg"},
            {"id": "email", "label": "E-mail", "type": "email"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is True, err


def test_schema_option_with_image_url_valid():
    """Options can be dicts with label/value/image_url."""
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "item", "label": "Item", "type": "radio",
             "options": [
                 {"label": "Hambúrguer", "value": "burger", "image_url": "https://example.com/b.jpg"},
                 {"label": "Pizza", "value": "pizza"},
             ]},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is True, err


def test_schema_option_with_html_in_label_rejected():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "item", "label": "Item", "type": "radio",
             "options": [{"label": "<b>Hambúrguer</b>", "value": "burger"}]},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "HTML" in err


def test_schema_image_display_with_local_url_valid():
    """image_display field with a /dashboard/form-image/ URL is valid."""
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "img", "label": "Img", "type": "image_display",
             "image_url": "/dashboard/form-image/abc123_form_xyz.jpg"},
            {"id": "email", "label": "E-mail", "type": "email"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is True, err


def test_schema_image_display_with_javascript_url_rejected():
    """image_display field with a javascript: URL must be rejected."""
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "img", "label": "Img", "type": "image_display",
             "image_url": "javascript:alert(1)"},
            {"id": "email", "label": "E-mail", "type": "email"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "URL" in err or "inválida" in err.lower()


def test_schema_image_display_with_data_url_rejected():
    """image_display field with a data: URL must be rejected."""
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "img", "label": "Img", "type": "image_display",
             "image_url": "data:image/png;base64,abc"},
            {"id": "email", "label": "E-mail", "type": "email"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False


def test_schema_option_image_url_javascript_rejected():
    """Option image_url with javascript: protocol must be rejected."""
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "item", "label": "Item", "type": "radio",
             "options": [
                 {"label": "Opção", "value": "opt", "image_url": "javascript:void(0)"},
             ]},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "URL" in err or "inválida" in err.lower()


def test_schema_condition_valid():
    # condition.field_id is a free-form string (the validator does not cross-check IDs)
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "type_q", "label": "Tipo", "type": "radio", "options": ["A", "B"]},
            {"id": "detail", "label": "Detalhe A", "type": "textarea",
             "condition": {"field_id": "type_q", "value": "A"}},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is True, err


def test_schema_condition_missing_value():
    schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text"},
            {"id": "email", "label": "E-mail", "type": "email",
             "condition": {"field_id": "name_0"}},   # missing 'value'
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "field_id" in err or "value" in err


def test_schema_duplicate_id_rejected():
    schema = {
        "fields": [
            {"id": "dup", "label": "Nome", "type": "text"},
            {"id": "dup", "label": "E-mail", "type": "email"},
        ]
    }
    valid, err = validate_custom_intake_schema(schema)
    assert valid is False
    assert "duplicado" in err


def test_v1_schema_backward_compatible():
    """Old v1 schemas (text/email/select only) must still validate."""
    v1_schema = {
        "fields": [
            {"id": "name", "label": "Nome", "type": "text", "required": True},
            {"id": "email", "label": "E-mail", "type": "email", "required": True},
            {"id": "crime", "label": "Natureza", "type": "select",
             "options": ["Furto", "Roubo", "Outro"]},
        ]
    }
    valid, err = validate_custom_intake_schema(v1_schema)
    assert valid is True, err


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

def test_custom_intake_template_model(app):
    with app.app_context():
        user = _make_user("u@test.com", "U")
        tpl = CustomIntakeTemplate(
            user_id=user.id,
            name="My Template",
            schema=_VALID_SCHEMA,
        )
        _db.session.add(tpl)
        _db.session.commit()

        fetched = CustomIntakeTemplate.query.get(tpl.id)
        assert fetched is not None
        assert fetched.name == "My Template"
        assert fetched.is_active is True
        assert fetched.user_id == user.id


def test_dashboard_session_has_intake_type(app):
    with app.app_context():
        user = _make_user("v@test.com", "V")
        sess = DashboardSession(
            user_id=user.id,
            label="Test",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
        )
        _db.session.add(sess)
        _db.session.commit()

        assert sess.intake_type == "police"
        assert sess.custom_template_id is None


def test_dashboard_session_custom_template_link(app):
    with app.app_context():
        user = _make_user("w@test.com", "W")
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="T", schema=_VALID_SCHEMA
        )
        _db.session.add(tpl)
        _db.session.commit()

        sess = DashboardSession(
            user_id=user.id,
            label="Test",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=12),
            intake_type="custom",
            custom_template_id=tpl.id,
        )
        _db.session.add(sess)
        _db.session.commit()

        assert sess.custom_template is not None
        assert sess.custom_template.name == "T"


# ---------------------------------------------------------------------------
# can_create_custom_template helper
# ---------------------------------------------------------------------------

def test_can_create_blocked_for_free_user(app):
    with app.app_context():
        user = _make_user("free@test.com", "Free", plan_type="free")
        from app.decorators import can_create_custom_template
        allowed, msg = can_create_custom_template(user)
        assert allowed is False
        assert "Enterprise" in msg


def test_can_create_blocked_for_premium_user(app):
    """Premium users cannot create custom templates — Enterprise only."""
    with app.app_context():
        user = _make_user("prem@test.com", "Prem", plan_type="premium")
        from app.decorators import can_create_custom_template
        allowed, msg = can_create_custom_template(user)
        assert allowed is False
        assert "Enterprise" in msg


def test_can_create_allowed_for_enterprise(app):
    with app.app_context():
        user = _make_user("ent@test.com", "Ent", plan_type="enterprise")
        from app.decorators import can_create_custom_template
        allowed, msg = can_create_custom_template(user)
        assert allowed is True
        assert msg is None


def test_can_create_blocked_when_limit_reached(app):
    with app.app_context():
        user = _make_user("lim@test.com", "Lim", plan_type="enterprise")
        for i in range(5):
            tpl = CustomIntakeTemplate(
                user_id=user.id, name=f"T{i}", schema=_VALID_SCHEMA
            )
            _db.session.add(tpl)
        _db.session.commit()

        from app.decorators import can_create_custom_template
        allowed, msg = can_create_custom_template(user)
        assert allowed is False
        assert "5" in msg


# ---------------------------------------------------------------------------
# Route tests (list, create, delete)
# ---------------------------------------------------------------------------

def test_list_custom_templates_requires_enterprise(app, client):
    with app.app_context():
        _make_user("free2@test.com", "Free2", plan_type="free")
    _login(client, "free2@test.com")
    resp = client.get("/dashboard/custom-templates", follow_redirects=True)
    assert b"Enterprise" in resp.data


def test_list_custom_templates_premium_user_blocked(app, client):
    """Premium users are redirected away from custom templates (Enterprise only)."""
    with app.app_context():
        _make_user("prem2@test.com", "Prem2", plan_type="premium")
    _login(client, "prem2@test.com")
    resp = client.get("/dashboard/custom-templates", follow_redirects=True)
    assert b"Enterprise" in resp.data


def test_list_custom_templates_enterprise_user(app, client):
    with app.app_context():
        _make_user("ent2@test.com", "Ent2", plan_type="enterprise")
    _login(client, "ent2@test.com")
    resp = client.get("/dashboard/custom-templates")
    assert resp.status_code == 200


def test_create_template_get(app, client):
    with app.app_context():
        _make_user("ent3@test.com", "Ent3", plan_type="enterprise")
    _login(client, "ent3@test.com")
    resp = client.get("/dashboard/custom-templates/create")
    assert resp.status_code == 200


def test_create_template_post_valid(app, client):
    import json
    with app.app_context():
        _make_user("ent4@test.com", "Ent4", plan_type="enterprise")
    _login(client, "ent4@test.com")
    resp = client.post(
        "/dashboard/custom-templates/create",
        data={
            "name": "My Custom Template",
            "schema_json": json.dumps(_VALID_SCHEMA),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"My Custom Template" in resp.data


def test_create_template_post_invalid_schema(app, client):
    import json
    with app.app_context():
        _make_user("ent5@test.com", "Ent5", plan_type="enterprise")
    _login(client, "ent5@test.com")
    bad_schema = {"fields": [{"id": "x", "label": "X", "type": "text"}]}
    resp = client.post(
        "/dashboard/custom-templates/create",
        data={
            "name": "Bad Template",
            "schema_json": json.dumps(bad_schema),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"inv" in resp.data.lower()


def test_delete_template(app, client):
    import json
    with app.app_context():
        user = _make_user("ent6@test.com", "Ent6", plan_type="enterprise")
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="ToDelete", schema=_VALID_SCHEMA
        )
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "ent6@test.com")
    resp = client.post(
        f"/dashboard/custom-templates/{tpl_id}/delete",
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        tpl = CustomIntakeTemplate.query.get(tpl_id)
        assert tpl.is_active is False


# ---------------------------------------------------------------------------
# Intake form with custom type
# ---------------------------------------------------------------------------

def test_custom_intake_form_renders(app, client):
    with app.app_context():
        user = _make_user("prem7@test.com", "Prem7", plan_type="premium")
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="Custom", schema=_VALID_SCHEMA
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

    resp = client.get(f"/t/{token}")
    assert resp.status_code == 200
    assert b"Nome" in resp.data


def test_custom_intake_submit(app, client):
    with app.app_context():
        user = _make_user("prem8@test.com", "Prem8", plan_type="premium")
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="Custom", schema=_VALID_SCHEMA
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

    resp = client.post(
        f"/t/{token}/submit",
        data={
            "field_name": "João da Silva",
            "field_email": "joao@test.com",
        },
        follow_redirects=False,
    )
    assert resp.status_code == 302
    assert f"/t/{token}/ok" in resp.location


def test_custom_intake_submit_required_field_missing(app, client):
    with app.app_context():
        user = _make_user("prem9@test.com", "Prem9", plan_type="premium")
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="Custom", schema=_VALID_SCHEMA
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

    # Missing required 'name' field
    resp = client.post(
        f"/t/{token}/submit",
        data={"field_email": "test@test.com"},
        follow_redirects=True,
    )
    # Should redirect back to form with flash message
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# New session creation with custom template
# ---------------------------------------------------------------------------

def test_new_session_with_custom_template(app, client):
    import json
    with app.app_context():
        user = _make_user("ent10@test.com", "Ent10", plan_type="enterprise")
        tpl = CustomIntakeTemplate(
            user_id=user.id, name="Custom Tpl", schema=_VALID_SCHEMA
        )
        _db.session.add(tpl)
        _db.session.commit()
        tpl_id = tpl.id

    _login(client, "ent10@test.com")
    resp = client.post(
        "/dashboard/sessions/new",
        data={
            "label": "Custom Session",
            "duration_hours": "3",
            "intake_type": "custom",
            "custom_template_id": str(tpl_id),
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200

    with app.app_context():
        sess = DashboardSession.query.filter_by(label="Custom Session").first()
        assert sess is not None
        assert sess.intake_type == "custom"
        assert sess.custom_template_id == tpl_id


def test_new_session_free_user_cannot_use_custom(app, client):
    with app.app_context():
        _make_user("free3@test.com", "Free3", plan_type="free")

    _login(client, "free3@test.com")
    resp = client.post(
        "/dashboard/sessions/new",
        data={
            "label": "Custom Session",
            "duration_hours": "3",
            "intake_type": "custom",
            "custom_template_id": "1",
        },
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert b"Premium" in resp.data
