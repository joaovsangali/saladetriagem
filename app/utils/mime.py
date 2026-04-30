"""MIME type detection from raw bytes."""


def detect_mimetype(data: bytes) -> str:
    """Return the MIME type for *data* based on its leading magic bytes."""
    if len(data) >= 5 and data[:5] == b'%PDF-':
        return "application/pdf"
    if len(data) >= 8 and data[:8] == b'\x89PNG\r\n\x1a\n':
        return "image/png"
    if len(data) >= 6 and data[:6] in (b'GIF87a', b'GIF89a'):
        return "image/gif"
    # JPEG (FF D8 FF) and unknown formats both fall back to JPEG
    return "image/jpeg"
