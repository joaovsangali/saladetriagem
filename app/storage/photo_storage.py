"""Abstract photo storage interface."""

import abc
from typing import Optional


class PhotoStorage(abc.ABC):
    """Interface that all photo storage backends must implement."""

    @abc.abstractmethod
    def save(self, photo_bytes: bytes, filename: str) -> str:
        """Persist *photo_bytes* and return a storage key/path."""

    @abc.abstractmethod
    def get_url(self, key: str) -> Optional[str]:
        """Return a URL (possibly signed) to access the photo, or None."""

    @abc.abstractmethod
    def download(self, key: str) -> Optional[bytes]:
        """Return the raw bytes for the photo identified by *key*, or None if not found."""

    @abc.abstractmethod
    def delete(self, key: str) -> None:
        """Delete the photo identified by *key*."""
