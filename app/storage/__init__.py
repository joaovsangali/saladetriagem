# app/storage/__init__.py
"""Storage backend factory.

Returns the appropriate PhotoStorage implementation based on STORAGE_BACKEND
config.  Defaults to LocalPhotoStorage when S3 credentials are not set so
that local/dev environments continue to work without any changes.
"""

import logging

logger = logging.getLogger(__name__)


def get_photo_storage(app=None):
    """Return a PhotoStorage instance configured from *app* (or environment).

    Priority:
    1. STORAGE_BACKEND=s3 AND S3_BUCKET + S3_ACCESS_KEY + S3_SECRET_KEY set
       → S3PhotoStorage
    2. Everything else → LocalPhotoStorage (safe fallback)

    If S3 initialisation fails for any reason, a warning is logged and the
    function falls back to LocalPhotoStorage to prevent the application from
    crashing.
    """
    if app is not None:
        backend = app.config.get("STORAGE_BACKEND", "local")
        upload_folder = app.config.get("UPLOAD_FOLDER", "uploads")
        bucket = app.config.get("S3_BUCKET", "")
        access_key = app.config.get("S3_ACCESS_KEY", "")
        secret_key = app.config.get("S3_SECRET_KEY", "")
        endpoint = app.config.get("S3_ENDPOINT", "")
        region = app.config.get("S3_REGION", "us-east-1")
        ttl = app.config.get("S3_SIGNED_URL_TTL", 3600)
    else:
        import os

        backend = os.environ.get("STORAGE_BACKEND", "local")
        upload_folder = os.environ.get("UPLOAD_FOLDER", "uploads")
        bucket = os.environ.get("S3_BUCKET", "")
        access_key = os.environ.get("S3_ACCESS_KEY", "")
        secret_key = os.environ.get("S3_SECRET_KEY", "")
        endpoint = os.environ.get("S3_ENDPOINT", "")
        region = os.environ.get("S3_REGION", "us-east-1")
        ttl = int(os.environ.get("S3_SIGNED_URL_TTL", "3600"))

    if backend == "s3" and bucket and access_key and secret_key:
        try:
            from app.storage.s3_storage import S3PhotoStorage

            storage = S3PhotoStorage(
                bucket=bucket,
                access_key=access_key,
                secret_key=secret_key,
                endpoint=endpoint,
                region=region,
                signed_url_ttl=ttl,
            )
            logger.info("Using S3 photo storage (bucket=%s)", bucket)
            return storage
        except Exception as exc:
            logger.warning(
                "Failed to initialise S3 storage (%s) — falling back to local",
                exc,
            )

    from app.storage.local_storage import LocalPhotoStorage

    logger.info("Using local photo storage (folder=%s)", upload_folder)
    return LocalPhotoStorage(upload_folder)
