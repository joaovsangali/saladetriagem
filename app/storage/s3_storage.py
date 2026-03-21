"""S3-compatible photo storage backend (AWS S3, MinIO, DigitalOcean Spaces)."""

import logging
import uuid
from typing import Optional

from app.storage.photo_storage import PhotoStorage

logger = logging.getLogger(__name__)


class S3PhotoStorage(PhotoStorage):
    """Upload photos to an S3-compatible bucket and return pre-signed URLs."""

    def __init__(
        self,
        bucket: str,
        access_key: str,
        secret_key: str,
        endpoint: str = "",
        region: str = "us-east-1",
        signed_url_ttl: int = 3600,
    ):
        import boto3

        self._bucket = bucket
        self._ttl = signed_url_ttl

        kwargs = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "region_name": region,
        }
        if endpoint:
            kwargs["endpoint_url"] = endpoint

        self._client = boto3.client("s3", **kwargs)

    def save(self, photo_bytes: bytes, filename: str) -> str:
        key = f"photos/{uuid.uuid4().hex}_{filename}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=photo_bytes,
            ContentType="image/jpeg",
        )
        logger.debug("Uploaded photo to S3: %s", key)
        return key

    def get_url(self, key: str) -> Optional[str]:
        try:
            url = self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=self._ttl,
            )
            return url
        except Exception as exc:
            logger.warning("Failed to generate S3 signed URL for %s: %s", key, exc)
            return None

    def delete(self, key: str) -> bool:
        """Delete a photo from S3 by key."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
            logger.debug("Deleted S3 object: %s", key)
            return True
        except Exception as exc:
            logger.error("Failed to delete S3 object %s: %s", key, exc)
            return False

    def health_check(self) -> bool:
        """Check if S3 is accessible."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
            return True
        except Exception:
            return False
