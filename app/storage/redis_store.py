"""Redis-backed submission store.

Submissions are serialised as JSON and stored with a 12-hour TTL.
Photos are stored as separate keys (binary, base64-encoded) to keep
the main submission entry small.
"""

import base64
import hashlib
import json
import logging
import re
import unicodedata
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)

_TTL = 12 * 60 * 60  # 12 hours in seconds
_KEY_PREFIX = "triagem:"


def _normalize_name(name: str) -> str:
    s = unicodedata.normalize("NFD", name.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z\s]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def _normalize_rg(rg: str) -> str:
    return re.sub(r"\D", "", rg)


class RedisSubmissionStore:
    """Redis-backed store with the same interface as the in-memory store."""

    def __init__(self, redis_client):
        self._r = redis_client

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sub_key(self, submission_id: str) -> str:
        return f"{_KEY_PREFIX}sub:{submission_id}"

    def _idx_key(self, dashboard_id: int) -> str:
        return f"{_KEY_PREFIX}idx:{dashboard_id}"

    def _dedup_key(self, dashboard_id: int) -> str:
        return f"{_KEY_PREFIX}dedup:{dashboard_id}"

    def _photo_key(self, submission_id: str, idx: int) -> str:
        return f"{_KEY_PREFIX}photo:{submission_id}:{idx}"

    def _dedup_keys_for(self, guest_name: str, rg: Optional[str]) -> list:
        keys = []
        norm_name = _normalize_name(guest_name)
        if norm_name:
            keys.append(f"name:{hashlib.sha256(norm_name.encode()).hexdigest()[:16]}")
        if rg:
            norm_rg = _normalize_rg(rg)
            if norm_rg:
                keys.append(f"rg:{hashlib.sha256(norm_rg.encode()).hexdigest()[:16]}")
        return keys

    def _serialize(self, submission) -> bytes:
        data = {
            "submission_id": submission.submission_id,
            "dashboard_id": submission.dashboard_id,
            "guest_name": submission.guest_name,
            "dob": submission.dob,
            "rg": submission.rg,
            "cpf": submission.cpf,
            "phone": submission.phone,
            "address": submission.address,
            "answers": submission.answers,
            "narrative": submission.narrative,
            "crime_type": submission.crime_type,
            "received_at": submission.received_at.isoformat(),
            "photo_count": len(submission.photos),
            "photo_keys": list(getattr(submission, "photo_keys", [])),
        }
        return json.dumps(data).encode()

    def _deserialize(self, raw: bytes, submission_id: str):
        from app.store import Submission

        data = json.loads(raw.decode())
        received_at = datetime.fromisoformat(data["received_at"])
        if received_at.tzinfo is None:
            received_at = received_at.replace(tzinfo=timezone.utc)

        photo_count = data.get("photo_count", 0)
        photos = []
        for i in range(photo_count):
            photo_raw = self._r.get(self._photo_key(submission_id, i))
            if photo_raw:
                photos.append(base64.b64decode(photo_raw))

        return Submission(
            submission_id=data["submission_id"],
            dashboard_id=data["dashboard_id"],
            guest_name=data["guest_name"],
            dob=data.get("dob"),
            rg=data.get("rg"),
            cpf=data.get("cpf"),
            phone=data.get("phone"),
            address=data.get("address"),
            answers=data.get("answers", {}),
            narrative=data.get("narrative"),
            crime_type=data["crime_type"],
            photos=photos,
            received_at=received_at,
            photo_keys=data.get("photo_keys", []),
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_duplicate(self, submission) -> bool:
        dedup_key = self._dedup_key(submission.dashboard_id)
        for dk in self._dedup_keys_for(submission.guest_name, submission.rg):
            if self._r.sismember(dedup_key, dk):
                return True
        return False

    def add(self, submission) -> str:
        sid = submission.submission_id
        pipe = self._r.pipeline()

        pipe.set(self._sub_key(sid), self._serialize(submission), ex=_TTL)
        pipe.rpush(self._idx_key(submission.dashboard_id), sid)
        pipe.expire(self._idx_key(submission.dashboard_id), _TTL)

        for i, photo_bytes in enumerate(submission.photos):
            pipe.set(
                self._photo_key(sid, i),
                base64.b64encode(photo_bytes),
                ex=_TTL,
            )

        dedup_key = self._dedup_key(submission.dashboard_id)
        for dk in self._dedup_keys_for(submission.guest_name, submission.rg):
            pipe.sadd(dedup_key, dk)
        pipe.expire(dedup_key, _TTL)

        pipe.execute()
        return sid

    def get(self, submission_id: str):
        raw = self._r.get(self._sub_key(submission_id))
        if raw is None:
            return None
        try:
            return self._deserialize(raw, submission_id)
        except Exception as exc:
            logger.warning("Failed to deserialize submission %s: %s", submission_id, exc)
            return None

    def list_for_dashboard(self, dashboard_id: int) -> list:
        ids = self._r.lrange(self._idx_key(dashboard_id), 0, -1)
        result = []
        for sid in ids:
            sid_str = sid.decode() if isinstance(sid, bytes) else sid
            sub = self.get(sid_str)
            if sub is not None:
                result.append(sub)
        return result

    def delete(self, submission_id: str):
        raw = self._r.get(self._sub_key(submission_id))
        if raw is None:
            return
        try:
            data = json.loads(raw.decode())
            dashboard_id = data["dashboard_id"]
            photo_count = data.get("photo_count", 0)
        except Exception:
            self._r.delete(self._sub_key(submission_id))
            return

        pipe = self._r.pipeline()
        pipe.delete(self._sub_key(submission_id))
        pipe.lrem(self._idx_key(dashboard_id), 1, submission_id)
        for i in range(photo_count):
            pipe.delete(self._photo_key(submission_id, i))
        pipe.execute()

    def purge_dashboard(self, dashboard_id: int):
        ids = self._r.lrange(self._idx_key(dashboard_id), 0, -1)
        pipe = self._r.pipeline()
        for sid in ids:
            sid_str = sid.decode() if isinstance(sid, bytes) else sid
            raw = self._r.get(self._sub_key(sid_str))
            pipe.delete(self._sub_key(sid_str))
            if raw:
                try:
                    data = json.loads(raw.decode())
                    photo_count = data.get("photo_count", 0)
                    for i in range(photo_count):
                        pipe.delete(self._photo_key(sid_str, i))
                except Exception:
                    pass
        pipe.delete(self._idx_key(dashboard_id))
        pipe.delete(self._dedup_key(dashboard_id))
        pipe.execute()

    def count_for_dashboard(self, dashboard_id: int) -> int:
        return self._r.llen(self._idx_key(dashboard_id))
