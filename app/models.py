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
    phone = db.Column(db.String(20), nullable=True)
    cpf = db.Column(db.String(20), nullable=True)
    phone_verified_at = db.Column(db.DateTime, nullable=True)
    plan_type = db.Column(db.String(20), default='trial')
    trial_ends_at = db.Column(db.DateTime, nullable=True)
    plan_usage_reset_at = db.Column(db.DateTime, nullable=True)
    # Legacy column kept for DB compatibility
    plan = db.Column(db.String(50), default="free")
    max_dashboards = db.Column(db.Integer, default=3)

    sessions = db.relationship("DashboardSession", backref="owner", lazy="dynamic")
    user_sessions = db.relationship("UserSession", backref="user", lazy="dynamic")
    plan_usages = db.relationship("PlanUsage", backref="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_trial_active(self):
        """Return True if the user is in an active trial period."""
        if self.plan_type != 'trial':
            return False
        if self.trial_ends_at is None:
            return False
        ends = self.trial_ends_at
        if ends.tzinfo is None:
            ends = ends.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) < ends

    def get_current_plan_limits(self):
        """Return the limits dict for the user's current effective plan."""
        from app.plans import PLANS
        if self.is_trial_active():
            return PLANS['trial']
        effective = self.plan_type if self.plan_type in PLANS else 'free'
        return PLANS[effective]

    def get_trial_info(self):
        """Return trial status dict for use in templates."""
        if not self.is_trial_active():
            return {'active': False}
        ends = self.trial_ends_at
        if ends.tzinfo is None:
            ends = ends.replace(tzinfo=timezone.utc)
        delta = ends - datetime.now(timezone.utc)
        days_left = max(0, delta.days)
        if days_left <= 3:
            warning_level = 'danger'
        elif days_left <= 7:
            warning_level = 'warning'
        elif days_left <= 15:
            warning_level = 'info'
        else:
            warning_level = 'secondary'
        return {
            'active': True,
            'days_left': days_left,
            'warning_level': warning_level,
            'ends_at': ends,
        }


class DashboardSession(db.Model):
    __tablename__ = "dashboard_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("police_users.id"), nullable=False)
    label = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    join_code = db.Column(db.String(6), unique=True, nullable=True, index=True)

    links = db.relationship("IntakeLink", backref="session", lazy="dynamic")
    logs = db.relationship("MinimalLogEntry", backref="session", lazy="dynamic")
    
    @staticmethod
    def make_expires_at():
        return datetime.now(timezone.utc) + timedelta(hours=12)
    
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


class AccessLog(db.Model):
    """Audit trail: every access to sensitive submission data is recorded here."""

    __tablename__ = "access_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("police_users.id"), nullable=False)
    # submission_id may be None for session-level actions
    submission_id = db.Column(db.String(64), nullable=True)
    # action: view | close | discard | download_photo | copy_text
    action = db.Column(db.String(50), nullable=False)
    accessed_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    ip_address = db.Column(db.String(45), nullable=True)   # IPv4 or IPv6
    user_agent = db.Column(db.String(256), nullable=True)

    user = db.relationship("PoliceUser", backref="access_logs")

    def __repr__(self):
        return f"<AccessLog user={self.user_id} action={self.action} sub={self.submission_id}>"


class UserSession(db.Model):
    """Tracks active login sessions for single-session enforcement."""

    __tablename__ = "user_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("police_users.id"), nullable=False)
    session_token = db.Column(db.String(64), unique=True, nullable=False,
                              default=lambda: secrets.token_urlsafe(32))
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    last_activity_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<UserSession user={self.user_id} active={self.is_active}>"


class SMSVerification(db.Model):
    """One-time SMS verification codes for phone verification."""

    __tablename__ = "sms_verifications"
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=False)
    verified_at = db.Column(db.DateTime, nullable=True)
    attempts = db.Column(db.Integer, default=0)

    @property
    def is_expired(self):
        exp = self.expires_at
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= exp

    @property
    def is_verified(self):
        return self.verified_at is not None

    def __repr__(self):
        return f"<SMSVerification phone={self.phone} verified={self.is_verified}>"


class PlanUsage(db.Model):
    """Monthly usage counters per user."""

    __tablename__ = "plan_usages"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("police_users.id"), nullable=False)
    month = db.Column(db.String(7), nullable=False)  # YYYY-MM
    sessions_created = db.Column(db.Integer, default=0)
    total_submissions = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'month', name='uq_plan_usage_user_month'),
    )

    def __repr__(self):
        return f"<PlanUsage user={self.user_id} month={self.month}>"


class SessionCollaborator(db.Model):
    """Vincula usuários convidados a sessões compartilhadas."""

    __tablename__ = "session_collaborators"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("dashboard_sessions.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("police_users.id"), nullable=False)
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('session_id', 'user_id', name='uq_session_collaborator'),
    )

    session = db.relationship("DashboardSession", backref="collaborators")
    user = db.relationship("PoliceUser")

    def __repr__(self):
        return f"<SessionCollaborator session={self.session_id} user={self.user_id}>"


class GlobalSMSCounter(db.Model):
    """Global monthly SMS send counter for anti-abuse limit."""

    __tablename__ = "global_sms_counters"
    id = db.Column(db.Integer, primary_key=True)
    month = db.Column(db.String(7), nullable=False, unique=True)  # YYYY-MM
    count = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<GlobalSMSCounter month={self.month} count={self.count}>"
