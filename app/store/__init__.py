import hashlib
import re
import threading
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


def _normalize_name(name: str) -> str:
    """Lowercase, strip accents via NFD, remove non-alpha, collapse spaces."""
    import unicodedata
    s = unicodedata.normalize("NFD", name.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _normalize_rg(rg: str) -> str:
    """Keep only digits."""
    return re.sub(r"\D", "", rg)


@dataclass
class Submission:
    submission_id: str
    dashboard_id: int
    guest_name: str
    dob: Optional[str]
    rg: Optional[str]
    cpf: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    answers: Dict
    narrative: Optional[str]
    crime_type: str
    photos: List[bytes]
    received_at: datetime
    # Storage keys for photos saved via photo_storage (S3 / local disk).
    # When set, photos bytes are not kept in memory.  Defaults to empty list
    # for backward compatibility with existing in-memory submissions.
    photo_keys: List[str] = field(default_factory=list)


class SubmissionStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._store: Dict[str, Submission] = {}  # submission_id -> Submission
        self._dashboard_index: Dict[int, List[str]] = {}  # dashboard_id -> [submission_ids]
        self._dedup_index: Dict[int, Set[str]] = {}
    
    def _dedup_keys(self, submission: Submission) -> list:
        keys = []
        norm_name = _normalize_name(submission.guest_name)
        if norm_name:
            keys.append(f"name:{hashlib.sha256(norm_name.encode()).hexdigest()[:16]}")
        if submission.rg:
            norm_rg = _normalize_rg(submission.rg)
            if norm_rg:
                keys.append(f"rg:{hashlib.sha256(norm_rg.encode()).hexdigest()[:16]}")
        return keys

    def is_duplicate(self, submission: Submission) -> bool:
        with self._lock:
            existing = self._dedup_index.get(submission.dashboard_id, set())
            for key in self._dedup_keys(submission):
                if key in existing:
                    return True
            return False

    def add(self, submission: Submission) -> str:
        with self._lock:
            sid = submission.submission_id
            self._store[sid] = submission
            if submission.dashboard_id not in self._dashboard_index:
                self._dashboard_index[submission.dashboard_id] = []
            self._dashboard_index[submission.dashboard_id].append(sid)
            if submission.dashboard_id not in self._dedup_index:
                self._dedup_index[submission.dashboard_id] = set()
            for key in self._dedup_keys(submission):
                self._dedup_index[submission.dashboard_id].add(key)
            return sid
    
    def get(self, submission_id: str) -> Optional[Submission]:
        with self._lock:
            return self._store.get(submission_id)
    
    def list_for_dashboard(self, dashboard_id: int) -> List[Submission]:
        with self._lock:
            ids = self._dashboard_index.get(dashboard_id, [])
            return [self._store[sid] for sid in ids if sid in self._store]
    
    def delete(self, submission_id: str):
        with self._lock:
            sub = self._store.pop(submission_id, None)
            if sub:
                ids = self._dashboard_index.get(sub.dashboard_id, [])
                if submission_id in ids:
                    ids.remove(submission_id)

    def purge_dashboard(self, dashboard_id: int):
        with self._lock:
            # Delete photos from external storage before purging
            try:
                from flask import current_app
                storage = getattr(current_app, "photo_storage", None)
                if storage:
                    ids = self._dashboard_index.get(dashboard_id, [])
                    for sid in ids:
                        sub = self._store.get(sid)
                        if sub and sub.photo_keys:
                            for key in sub.photo_keys:
                                try:
                                    storage.delete(key)
                                except Exception:
                                    pass
            except RuntimeError:
                pass  # No application context (e.g. tests)

            ids = self._dashboard_index.pop(dashboard_id, [])
            for sid in ids:
                self._store.pop(sid, None)
            self._dedup_index.pop(dashboard_id, None)
    
    def count_for_dashboard(self, dashboard_id: int) -> int:
        with self._lock:
            return len([sid for sid in self._dashboard_index.get(dashboard_id, []) if sid in self._store])


def _build_store():
    """Return a Redis-backed store if Redis is available, else in-memory."""
    try:
        from app.redis_client import get_redis_client
        from app.storage.redis_store import RedisSubmissionStore

        client = get_redis_client()
        if client is not None:
            import logging
            logging.getLogger(__name__).info("Using Redis-backed submission store")
            return RedisSubmissionStore(client)
    except Exception:
        pass
    return SubmissionStore()


submission_store = _build_store()

