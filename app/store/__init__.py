import threading
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional

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
    
    def add(self, submission: Submission) -> str:
        with self._lock:
            sid = submission.submission_id
            self._store[sid] = submission
            if submission.dashboard_id not in self._dashboard_index:
                self._dashboard_index[submission.dashboard_id] = []
            self._dashboard_index[submission.dashboard_id].append(sid)
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
    
    def count_for_dashboard(self, dashboard_id: int) -> int:
        with self._lock:
            return len([sid for sid in self._dashboard_index.get(dashboard_id, []) if sid in self._store])

submission_store = SubmissionStore()
