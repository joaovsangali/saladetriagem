import secrets
from datetime import datetime, timedelta, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db

class PoliceUser(UserMixin, db.Model):
    __tablename__ = "police_users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    plan = db.Column(db.String(50), default="free")
    max_dashboards = db.Column(db.Integer, default=3)
    
    sessions = db.relationship("DashboardSession", backref="owner", lazy="dynamic")
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class DashboardSession(db.Model):
    __tablename__ = "dashboard_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("police_users.id"), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    links = db.relationship("IntakeLink", backref="session", lazy="dynamic")
    logs = db.relationship("MinimalLogEntry", backref="session", lazy="dynamic")
    
    @staticmethod
    def make_expires_at():
        return datetime.now(timezone.utc) + timedelta(hours=24)
    
    @property
    def is_expired(self):
        expires = self.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expires


class IntakeLink(db.Model):
    __tablename__ = "intake_links"
    id = db.Column(db.Integer, primary_key=True)
    dashboard_id = db.Column(db.Integer, db.ForeignKey("dashboard_sessions.id"), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    form_schema = db.Column(db.JSON, nullable=False)


class MinimalLogEntry(db.Model):
    __tablename__ = "minimal_log_entries"
    id = db.Column(db.Integer, primary_key=True)
    dashboard_id = db.Column(db.Integer, db.ForeignKey("dashboard_sessions.id"), nullable=False)
    police_user_id = db.Column(db.Integer, db.ForeignKey("police_users.id"), nullable=False)
    guest_display_name = db.Column(db.String(200))
    crime_type = db.Column(db.String(100))
    received_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="received")  # received, closed, discarded
