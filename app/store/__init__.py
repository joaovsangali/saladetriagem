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
    address: Optional[str]
    answers: Dict
    narrative: Optional[str]
    crime_type: str
    photos: List[bytes]
    received_at: datetime

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
            ids = self._dashboard_index.pop(dashboard_id, [])
            for sid in ids:
                self._store.pop(sid, None)
            self._dedup_index.pop(dashboard_id, None)
    
    def count_for_dashboard(self, dashboard_id: int) -> int:
        with self._lock:
            return len([sid for sid in self._dashboard_index.get(dashboard_id, []) if sid in self._store])

submission_store = SubmissionStore()
