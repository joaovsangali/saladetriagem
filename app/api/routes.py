import base64
import uuid
from datetime import datetime, timezone
from flask import jsonify, abort, request, Response
from flask_login import login_required, current_user
from app.api import api_bp
from app.extensions import db
from app.models import DashboardSession, MinimalLogEntry
from app.store import submission_store
from app.renderer.text import TextRenderer
from app.schemas.crime_types import CRIME_SCHEMAS

def _get_owned_session(session_id):
    return DashboardSession.query.filter_by(
        id=session_id, user_id=current_user.id
    ).first_or_404()

@api_bp.route("/sessions/<int:session_id>/submissions")
@login_required
def list_submissions(session_id):
    _get_owned_session(session_id)
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
    session = _get_owned_session(session_id)
    sub = submission_store.get(submission_id)
    if not sub or sub.dashboard_id != session_id:
        abort(404)
    
    questions = CRIME_SCHEMAS.get(sub.crime_type, {}).get("questions", [])
    structured = TextRenderer.render_structured(sub, questions)
    text = TextRenderer.render(sub)
    
    return jsonify({
        "id": sub.submission_id,
        "guest_name": sub.guest_name,
        "dob": sub.dob,
        "rg": sub.rg,
        "cpf": sub.cpf,
        "address": sub.address,
        "crime_type": sub.crime_type,
        "narrative": sub.narrative,
        "answers": sub.answers,
        "received_at": sub.received_at.isoformat(),
        "photo_count": len(sub.photos),
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
    submission_store.delete(submission_id)
    db.session.commit()
    
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
    submission_store.delete(submission_id)
    db.session.commit()
    
    return jsonify({"status": "ok"})

@api_bp.route("/sessions/<int:session_id>/submissions/<submission_id>/photo/<int:index>")
@login_required
def get_photo(session_id, submission_id, index):
    session = _get_owned_session(session_id)
    sub = submission_store.get(submission_id)
    if not sub or sub.dashboard_id != session_id:
        abort(404)
    if index < 0 or index >= len(sub.photos):
        abort(404)
    
    return Response(
        sub.photos[index],
        mimetype="image/jpeg",
        headers={"Cache-Control": "no-store"},
    )
