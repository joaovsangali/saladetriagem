"""Local filesystem photo storage backend."""

import logging
import os
import uuid
from typing import Optional

from app.storage.photo_storage import PhotoStorage

logger = logging.getLogger(__name__)


class LocalPhotoStorage(PhotoStorage):
    """Store photos on the local filesystem inside *upload_folder*."""

    def __init__(self, upload_folder: str):
        self._folder = upload_folder
        os.makedirs(self._folder, exist_ok=True)

    def save(self, photo_bytes: bytes, filename: str) -> str:
        key = f"{uuid.uuid4().hex}_{filename}"
        path = os.path.join(self._folder, key)
        with open(path, "wb") as fh:
            fh.write(photo_bytes)
        return key

    def get_url(self, key: str) -> Optional[str]:
        # Local files are served via the proxy route; no external URL needed.
        return None

    def download(self, key: str) -> Optional[bytes]:
        path = os.path.join(self._folder, key)
        try:
            with open(path, "rb") as fh:
                return fh.read()
        except FileNotFoundError:
            return None
        except OSError as exc:
            logger.warning("Error reading photo %s: %s", key, exc)
            return None

    def delete(self, key: str) -> None:
        path = os.path.join(self._folder, key)
        try:
            os.remove(path)
        except FileNotFoundError:
            logger.debug("Photo not found for deletion: %s", key)
        except OSError as exc:
            logger.warning("Error deleting photo %s: %s", key, exc)
