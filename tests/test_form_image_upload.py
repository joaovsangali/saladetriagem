"""Tests for the form-builder image upload and serve routes."""
import io
import os
import struct
import tempfile
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


def _make_minimal_png() -> bytes:
    """Return a valid 1×1 pixel PNG image in bytes."""
    import zlib

    def png_chunk(name: bytes, data: bytes) -> bytes:
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", zlib.crc32(name + data) & 0xFFFFFFFF)
        return length + name + data + crc

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = png_chunk(b"IHDR", ihdr_data)
    raw_row = b"\x00\xff\xff\xff"  # filter byte + RGB pixel
    idat = png_chunk(b"IDAT", zlib.compress(raw_row))
    iend = png_chunk(b"IEND", b"")
    return signature + ihdr + idat + iend


def _make_minimal_jpeg() -> bytes:
    """Return a minimal valid JPEG (SOI + EOI markers only)."""
    return b"\xff\xd8\xff\xe0" + b"\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\xff\xd9"


def _make_minimal_gif() -> bytes:
    """Return a minimal valid GIF89a 1×1 image."""
    return (
        b"GIF89a"
        b"\x01\x00\x01\x00\x80\x00\x00"  # header + palette flag
        b"\xff\xff\xff"  # background colour (white)
        b"\x00\x00\x00"  # palette entry 0 (black)
        b"\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00"  # image descriptor
        b"\x02\x02\x4c\x01\x00"  # image data
        b"\x3b"  # trailer
    )


@pytest.fixture()
def app():
    with tempfile.TemporaryDirectory() as tmpdir:
        config = type("Cfg", (TestConfig,), {"UPLOAD_FOLDER": tmpdir})
        application = create_app(config)
        with application.app_context():
            _db.create_all()
            yield application
            _db.session.remove()
            _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def _make_user(email="uploader@test.com", plan_type="enterprise"):
    user = PoliceUser(
        email=email,
        display_name="Uploader",
        is_active=True,
        plan_type=plan_type,
    )
    user.set_password("senha1234")
    _db.session.add(user)
    _db.session.commit()
    return user


def _login(client, email="uploader@test.com"):
    return client.post("/login", data={"email": email, "password": "senha1234"})


# ── upload-image endpoint ──────────────────────────────────────────────────

class TestUploadImage:
    def test_requires_login(self, app, client):
        """Unauthenticated requests must be redirected."""
        resp = client.post(
            "/dashboard/upload-image",
            data={"image": (io.BytesIO(b""), "test.png")},
            content_type="multipart/form-data",
        )
        assert resp.status_code in (302, 401)

    def test_missing_file_returns_400(self, app, client):
        with app.app_context():
            _make_user()
        _login(client)
        resp = client.post("/dashboard/upload-image", data={}, content_type="multipart/form-data")
        assert resp.status_code == 400
        assert b"Nenhum" in resp.data

    def test_upload_valid_png(self, app, client):
        with app.app_context():
            _make_user()
        _login(client)
        png = _make_minimal_png()
        resp = client.post(
            "/dashboard/upload-image",
            data={"image": (io.BytesIO(png), "photo.png")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "url" in data
        assert "/dashboard/form-image/" in data["url"]

    def test_upload_valid_gif(self, app, client):
        with app.app_context():
            _make_user()
        _login(client)
        gif = _make_minimal_gif()
        resp = client.post(
            "/dashboard/upload-image",
            data={"image": (io.BytesIO(gif), "anim.gif")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert "url" in data

    def test_oversized_file_rejected(self, app, client):
        with app.app_context():
            _make_user()
        _login(client)
        big = b"\xff\xd8\xff" + b"\x00" * (3 * 1024 * 1024)  # ~3 MB fake JPEG
        resp = client.post(
            "/dashboard/upload-image",
            data={"image": (io.BytesIO(big), "big.jpg")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400

    def test_invalid_type_rejected(self, app, client):
        with app.app_context():
            _make_user()
        _login(client)
        resp = client.post(
            "/dashboard/upload-image",
            data={"image": (io.BytesIO(b"not an image"), "evil.exe")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 400


# ── serve-form-image endpoint ──────────────────────────────────────────────

class TestServeFormImage:
    def test_serve_uploaded_image(self, app, client):
        """After upload, the returned URL should serve the image (no auth required)."""
        with app.app_context():
            _make_user()
        _login(client)
        png = _make_minimal_png()
        upload_resp = client.post(
            "/dashboard/upload-image",
            data={"image": (io.BytesIO(png), "serve_test.png")},
            content_type="multipart/form-data",
        )
        assert upload_resp.status_code == 200
        url = upload_resp.get_json()["url"]

        # Serve without authentication (simulates intake form)
        with app.test_client() as anon_client:
            serve_resp = anon_client.get(url)
        assert serve_resp.status_code == 200

    def test_nonexistent_key_returns_404(self, app, client):
        serve_resp = client.get("/dashboard/form-image/nonexistent_key_xyz.png")
        assert serve_resp.status_code == 404
