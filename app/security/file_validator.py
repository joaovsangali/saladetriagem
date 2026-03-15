"""File upload validation using magic bytes, size, and dimension checks."""

import io
import logging
import struct
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Magic bytes for allowed image types
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

# Maximum allowed image dimensions (width × height)
_MAX_DIMENSION = 8000  # pixels

# Maximum file size in bytes (overridable)
_DEFAULT_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


class FileValidationError(ValueError):
    """Raised when a file fails validation."""


def validate_image(
    data: bytes,
    max_size_bytes: int = _DEFAULT_MAX_SIZE,
    allowed_mimetypes: Optional[Tuple[str, ...]] = None,
) -> str:
    """Validate *data* as a safe image upload.

    Returns the detected MIME type (``"image/jpeg"`` or ``"image/png"``).
    Raises :class:`FileValidationError` on any validation failure.
    """
    if allowed_mimetypes is None:
        allowed_mimetypes = ("image/jpeg", "image/png")

    # 1. Size check
    if len(data) > max_size_bytes:
        raise FileValidationError(
            f"File too large: {len(data)} bytes (max {max_size_bytes})"
        )

    # 2. Magic bytes check
    mime = _detect_mime(data)
    if mime not in allowed_mimetypes:
        raise FileValidationError(
            f"File type not allowed: {mime}. Allowed: {allowed_mimetypes}"
        )

    # 3. Image dimension check using Pillow
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        img.verify()  # raises if data is corrupt
    except Exception as exc:
        raise FileValidationError(f"Invalid or corrupt image: {exc}") from exc

    # Re-open after verify (PIL requires re-open after verify)
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(data))
        w, h = img.size
        if w > _MAX_DIMENSION or h > _MAX_DIMENSION:
            raise FileValidationError(
                f"Image dimensions too large: {w}×{h} (max {_MAX_DIMENSION})"
            )
    except FileValidationError:
        raise
    except Exception as exc:
        raise FileValidationError(f"Could not read image dimensions: {exc}") from exc

    return mime


def _detect_mime(data: bytes) -> str:
    """Detect MIME type from magic bytes."""
    if data[:3] == _JPEG_MAGIC:
        return "image/jpeg"
    if data[:8] == _PNG_MAGIC:
        return "image/png"
    return "application/octet-stream"
