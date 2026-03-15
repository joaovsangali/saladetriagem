"""Tests for the production-ready infrastructure additions."""

import json
import pytest

from app import create_app
from app.extensions import db as _db
from app.models import PoliceUser


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


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_json(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert "status" in data
        assert "db" in data

    def test_health_status_ok_when_db_available(self, client):
        resp = client.get("/health")
        data = json.loads(resp.data)
        assert data["status"] == "ok"
        assert data["db"] is True


# ---------------------------------------------------------------------------
# Request ID middleware
# ---------------------------------------------------------------------------

class TestRequestIDMiddleware:
    def test_response_contains_request_id_header(self, client):
        resp = client.get("/health")
        assert "X-Request-ID" in resp.headers

    def test_request_id_is_non_empty(self, client):
        resp = client.get("/health")
        assert len(resp.headers["X-Request-ID"]) > 0

    def test_custom_request_id_is_echoed(self, client):
        resp = client.get(
            "/health", headers={"X-Request-ID": "my-custom-id-123"}
        )
        assert resp.headers["X-Request-ID"] == "my-custom-id-123"


# ---------------------------------------------------------------------------
# In-memory submission store (backward compatibility)
# ---------------------------------------------------------------------------

class TestSubmissionStore:
    def test_in_memory_store_is_used_without_redis(self):
        from app.store import SubmissionStore, submission_store
        # When Redis is not configured, the store should be an in-memory store
        assert isinstance(submission_store, SubmissionStore)

    def test_submission_store_add_and_get(self):
        from datetime import datetime, timezone
        from app.store import Submission, SubmissionStore

        store = SubmissionStore()
        sub = Submission(
            submission_id="test-123",
            dashboard_id=1,
            guest_name="Test User",
            dob=None,
            rg=None,
            cpf=None,
            phone=None,
            address=None,
            answers={},
            narrative=None,
            crime_type="outros",
            photos=[],
            received_at=datetime.now(timezone.utc),
        )
        store.add(sub)
        retrieved = store.get("test-123")
        assert retrieved is not None
        assert retrieved.guest_name == "Test User"

    def test_duplicate_detection_by_name(self):
        from datetime import datetime, timezone
        from app.store import Submission, SubmissionStore

        store = SubmissionStore()
        base = dict(
            dashboard_id=1,
            dob=None, rg=None, cpf=None, phone=None, address=None,
            answers={}, narrative=None, crime_type="outros", photos=[],
            received_at=datetime.now(timezone.utc),
        )
        sub1 = Submission(submission_id="a1", guest_name="João Silva", **base)
        sub2 = Submission(submission_id="a2", guest_name="João Silva", **base)
        store.add(sub1)
        assert store.is_duplicate(sub2)

    def test_no_duplicate_different_names(self):
        from datetime import datetime, timezone
        from app.store import Submission, SubmissionStore

        store = SubmissionStore()
        base = dict(
            dashboard_id=1,
            dob=None, rg=None, cpf=None, phone=None, address=None,
            answers={}, narrative=None, crime_type="outros", photos=[],
            received_at=datetime.now(timezone.utc),
        )
        sub1 = Submission(submission_id="b1", guest_name="Maria Silva", **base)
        sub2 = Submission(submission_id="b2", guest_name="José Santos", **base)
        store.add(sub1)
        assert not store.is_duplicate(sub2)


# ---------------------------------------------------------------------------
# File validator
# ---------------------------------------------------------------------------

class TestFileValidator:
    def test_rejects_file_exceeding_max_size(self):
        from app.security.file_validator import FileValidationError, validate_image

        large_data = b"\xff\xd8\xff" + b"x" * (11 * 1024 * 1024)  # 11 MB JPEG-magic
        with pytest.raises(FileValidationError, match="too large"):
            validate_image(large_data, max_size_bytes=10 * 1024 * 1024)

    def test_rejects_non_image_file(self):
        from app.security.file_validator import FileValidationError, validate_image

        with pytest.raises(FileValidationError):
            validate_image(b"PK\x03\x04" + b"zip content")  # ZIP magic bytes

    def test_detects_jpeg_magic_bytes(self):
        from app.security.file_validator import _detect_mime

        assert _detect_mime(b"\xff\xd8\xff" + b"\x00" * 10) == "image/jpeg"

    def test_detects_png_magic_bytes(self):
        from app.security.file_validator import _detect_mime

        assert _detect_mime(b"\x89PNG\r\n\x1a\n" + b"\x00" * 10) == "image/png"

    def test_unknown_magic_bytes(self):
        from app.security.file_validator import _detect_mime

        assert _detect_mime(b"\x00\x01\x02\x03") == "application/octet-stream"


# ---------------------------------------------------------------------------
# In-memory rate limiter
# ---------------------------------------------------------------------------

class TestInMemoryRateLimiter:
    def test_allows_requests_within_limit(self):
        from app.security.rate_limit import InMemoryRateLimiter

        rl = InMemoryRateLimiter()
        for _ in range(5):
            assert rl.is_allowed("test-key", limit=5, window_seconds=60)

    def test_blocks_after_limit_exceeded(self):
        from app.security.rate_limit import InMemoryRateLimiter

        rl = InMemoryRateLimiter()
        for _ in range(5):
            rl.is_allowed("key2", limit=5, window_seconds=60)
        assert not rl.is_allowed("key2", limit=5, window_seconds=60)

    def test_different_keys_are_independent(self):
        from app.security.rate_limit import InMemoryRateLimiter

        rl = InMemoryRateLimiter()
        for _ in range(5):
            rl.is_allowed("key-a", limit=5, window_seconds=60)
        # key-b should still be allowed
        assert rl.is_allowed("key-b", limit=5, window_seconds=60)


# ---------------------------------------------------------------------------
# Config — PostgreSQL pool options
# ---------------------------------------------------------------------------

class TestConfigPoolOptions:
    def test_sqlite_has_no_pool_size(self):
        from config import Config

        opts = Config.SQLALCHEMY_ENGINE_OPTIONS
        assert "pool_size" not in opts
        assert "max_overflow" not in opts

    def test_sqlite_has_pool_pre_ping(self):
        from config import Config

        opts = Config.SQLALCHEMY_ENGINE_OPTIONS
        assert opts.get("pool_pre_ping") is True


# ---------------------------------------------------------------------------
# WSGI — wsgi.py entry point
# ---------------------------------------------------------------------------

class TestWsgiEntryPoint:
    def test_wsgi_module_exposes_app(self):
        import importlib
        import sys
        import os

        # Temporarily set a valid SECRET_KEY and non-production env
        os.environ.setdefault("SECRET_KEY", "test-wsgi-key-1234567890abcdef1234567890ab")
        os.environ["FLASK_ENV"] = "development"

        # If already imported, reload to use the new env
        if "wsgi" in sys.modules:
            del sys.modules["wsgi"]

        import wsgi
        assert hasattr(wsgi, "app")
        assert wsgi.app is not None
