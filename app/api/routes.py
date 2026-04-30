import base64
import uuid
from datetime import datetime, timezone
from flask import jsonify, abort, request, Response, redirect, current_app
from flask_login import login_required, current_user
from app.api import api_bp
from app.extensions import db
from app.models import DashboardSession, MinimalLogEntry
from app.store import submission_store
from app.renderer.text import TextRenderer
from app.schemas.crime_types import CRIME_SCHEMAS
from app.audit import log_access
from app.utils.access_control import can_access_session
from app.utils.mime import detect_mimetype

def _get_owned_session(session_id):
    return DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

@api_bp.route("/sessions/<int:session_id>/submissions")
@login_required
def list_submissions(session_id):
    session = DashboardSession.query.get_or_404(session_id)
    can_access, role = can_access_session(current_user, session)
    if not can_access:
        abort(403)
    subs = submission_store.list_for_dashboard(session_id)
    return jsonify([{
        "id": s.submission_id,
        "guest_name": s.guest_name,
        "crime_type": s.crime_type,
        "received_at": s.received_at.isoformat(),
    } for s in subs])

@api_bp.route("/sessions/<int:session_id>/submissions/<submission_id>")
@login_required
def get_submission(session_id, submission_id):
    session = DashboardSession.query.get_or_404(session_id)
    can_access, role = can_access_session(current_user, session)
    if not can_access:
        abort(403)
    sub = submission_store.get(submission_id)
    if not sub or sub.dashboard_id != session_id:
        abort(404)

    log_access(current_user, submission_id, "view")

    questions = CRIME_SCHEMAS.get(sub.crime_type, {}).get("questions", [])
    structured = TextRenderer.render_structured(sub, questions)
    text = TextRenderer.render(sub)

    photo_keys = list(getattr(sub, "photo_keys", []))
    
    return jsonify({
        "id": sub.submission_id,
        "guest_name": sub.guest_name,
        "dob": sub.dob,
        "rg": sub.rg,
        "cpf": sub.cpf,
        "phone": sub.phone,
        "address": sub.address,
        "crime_type": sub.crime_type,
        "narrative": sub.narrative,
        "answers": sub.answers,
        "received_at": sub.received_at.isoformat(),
        # Total photo count = S3 keys + in-memory bytes (may be mixed on
        # partial S3 failure; see intake route for details).
        "photo_count": len(photo_keys) + len(sub.photos),
        "structured": structured,
        "text": text,
    })

@api_bp.route("/sessions/<int:session_id>/submissions/<submission_id>/close", methods=["POST"])
@login_required
def close_submission(session_id, submission_id):
    session = _get_owned_session(session_id)
    sub = submission_store.get(submission_id)
    if not sub or sub.dashboard_id != session_id:
        abort(404)
    
    log = MinimalLogEntry(
        dashboard_id=session_id,
        police_user_id=current_user.id,
        guest_display_name=sub.guest_name,
        crime_type=sub.crime_type,
        received_at=sub.received_at,
        closed_at=datetime.now(timezone.utc),
        status="closed",
    )
    db.session.add(log)

    # Delete photos from S3
    storage = getattr(current_app, "photo_storage", None)
    if storage and sub.photo_keys:
        for key in sub.photo_keys:
            storage.delete(key)

    submission_store.delete(submission_id)
    db.session.commit()

    log_access(current_user, submission_id, "close")

    return jsonify({"status": "ok"})

@api_bp.route("/sessions/<int:session_id>/submissions/<submission_id>/discard", methods=["POST"])
@login_required
def discard_submission(session_id, submission_id):
    session = _get_owned_session(session_id)
    sub = submission_store.get(submission_id)
    if not sub or sub.dashboard_id != session_id:
        abort(404)
    
    log = MinimalLogEntry(
        dashboard_id=session_id,
        police_user_id=current_user.id,
        guest_display_name=sub.guest_name,
        crime_type=sub.crime_type,
        received_at=sub.received_at,
        closed_at=datetime.now(timezone.utc),
        status="discarded",
    )
    db.session.add(log)

    # Delete photos from S3
    storage = getattr(current_app, "photo_storage", None)
    if storage and sub.photo_keys:
        for key in sub.photo_keys:
            storage.delete(key)

    submission_store.delete(submission_id)
    db.session.commit()

    log_access(current_user, submission_id, "discard")

    return jsonify({"status": "ok"})

@api_bp.route("/sessions/<int:session_id>/submissions/<submission_id>/photo/<int:index>")
@login_required
def get_photo(session_id, submission_id, index):
    # Enforce plan: free users cannot view photos
    if not current_user.get_current_plan_limits().get('can_view_photos'):
        abort(403)

    session = DashboardSession.query.get_or_404(session_id)
    can_access, role = can_access_session(current_user, session)
    if not can_access:
        abort(403)
    sub = submission_store.get(submission_id)
    if not sub or sub.dashboard_id != session_id:
        abort(404)

    log_access(current_user, submission_id, "download_photo")

    photo_keys = list(getattr(sub, "photo_keys", []))

    # Photos are split between S3-backed keys (photo_keys) and in-memory bytes
    # (sub.photos).  S3 keys come first (index 0 .. len(photo_keys)-1) and
    # in-memory bytes follow (index len(photo_keys) .. total-1).
    total_keys = len(photo_keys)
    total_bytes = len(sub.photos)
    total = total_keys + total_bytes

    if index < 0 or index >= total:
        abort(404)

    if index < total_keys:
        # Photo is in external storage — proxy bytes to the client so the
        # browser always loads images from 'self' (required by the CSP).
        storage = getattr(current_app, "photo_storage", None)
        if storage is not None:
            data_bytes = storage.download(photo_keys[index])
            if data_bytes:
                mime = detect_mimetype(data_bytes)
                ext = "pdf" if mime == "application/pdf" else "jpg"
                headers = {"Cache-Control": "no-store"}
                if request.args.get("download") == "1":
                    headers["Content-Disposition"] = f"attachment; filename=photo_{index}.{ext}"
                return Response(data_bytes, mimetype=mime, headers=headers)
        abort(404)

    # Photo is in memory (local / Redis path).
    mem_index = index - total_keys
    data_bytes = sub.photos[mem_index]
    mime = detect_mimetype(data_bytes)
    ext = "pdf" if mime == "application/pdf" else "jpg"
    headers = {"Cache-Control": "no-store"}
    if request.args.get("download") == "1":
        headers["Content-Disposition"] = f"attachment; filename=photo_{index}.{ext}"
    return Response(data_bytes, mimetype=mime, headers=headers)


