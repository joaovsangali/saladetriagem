import logging
import os
from datetime import timezone, timedelta
from flask import Flask
from config import Config
from app.extensions import db, login_manager, csrf, limiter, migrate
from app.models import PoliceUser
from app.cli import register_cli
from app.middleware import HTTPSRedirectMiddleware, RequestIDMiddleware
from app.security_headers import add_security_headers
from app.errors import register_error_handlers
from app.log_sanitizer import SanitizingFilter

logger = logging.getLogger(__name__)

_DEFAULT_SECRET_KEY = "dev-secret-change-in-prod"
_MIN_SECRET_KEY_LENGTH = 32

# Try to use proper IANA timezone (requires tzdata on Windows).
# Fall back to a fixed UTC-3 offset — Brazil dropped DST in 2019, so
# America/Sao_Paulo is permanently UTC-3.
try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    _SP_TZ = ZoneInfo("America/Sao_Paulo")
    _UTC_TZ = ZoneInfo("UTC")
except (ImportError, KeyError):
    # Windows has no system tz database; install tzdata to get proper IANA zones.
    # Brazil dropped DST in 2019, so UTC-3 is permanently correct for São Paulo.
    _SP_TZ = timezone(timedelta(hours=-3))
    _UTC_TZ = timezone.utc


def _datefmt(value, fmt="dd/mm/yyyy HH:MM"):
    """Jinja2 filter: format a datetime in Brazilian style (America/Sao_Paulo)."""
    if value is None:
        return "—"
    if value.tzinfo is None:
        value = value.replace(tzinfo=_UTC_TZ)
    value = value.astimezone(_SP_TZ)
    if fmt == "dd/mm/yyyy HH:MM":
        return value.strftime("%d/%m/%Y %H:%M")
    if fmt == "dd/mm/yyyy":
        return value.strftime("%d/%m/%Y")
    if fmt == "dd/mm HH:MM":
        return value.strftime("%d/%m %H:%M")
    return value.strftime(fmt)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Run class-level init (e.g. ProductionConfig validates SECRET_KEY)
    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    # Global SECRET_KEY validation — independent of config class.
    # In production (FLASK_ENV=production) a weak key is a hard error.
    # In development/testing, emit a visible warning but allow boot.
    _secret = app.config.get("SECRET_KEY", "")
    _is_production = os.environ.get("FLASK_ENV", "development") == "production"
    if _secret == _DEFAULT_SECRET_KEY or len(_secret) < _MIN_SECRET_KEY_LENGTH:
        if _is_production:
            raise ValueError(
                "ERRO CRÍTICO: SECRET_KEY inválida para produção. "
                "Gere uma chave segura com: "
                "python -c \"import secrets; print(secrets.token_urlsafe(64))\" "
                "e configure via variável de ambiente SECRET_KEY."
            )
        logger.warning(
            "Using default or weak SECRET_KEY. Set the SECRET_KEY environment "
            "variable before deploying to production."
        )

    app.jinja_env.filters["datefmt"] = _datefmt
    from datetime import datetime as _datetime
    app.jinja_env.globals["now"] = _datetime.now

    # Structured logging with PII sanitization (non-debug mode)
    if not app.debug:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        handler.addFilter(SanitizingFilter())
        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Faça login para continuar."
    login_manager.login_message_category = "warning"
    
    @login_manager.user_loader
    def load_user(user_id):
        return PoliceUser.query.get(int(user_id))
    
    # Blueprints
    from app.auth import auth_bp
    from app.dashboard import dashboard_bp
    from app.api import api_bp
    from app.intake import intake_bp
    from app.account import account_bp
    from app.plans_page import plans_page_bp
    from app.public import public_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(intake_bp)
    app.register_blueprint(account_bp)
    app.register_blueprint(plans_page_bp)
    app.register_blueprint(public_bp)

    # Session validation: enforce single active session per user
    from flask import request as _request, session as _session
    from flask_login import current_user as _cu, logout_user as _lu

    @app.before_request
    def validate_user_session():
        """Invalidate session if the token is no longer active in DB."""
        if not _cu.is_authenticated:
            return None
        # Skip static files and auth routes
        if _request.endpoint and (
            _request.endpoint.startswith('static')
            or _request.endpoint in ('auth.login', 'auth.logout', 'auth.register',
                                     'auth.confirm_email', 'auth.resend_confirmation',
                                     'auth.verify_phone', 'auth.verify_phone_submit',
                                     'auth.resend_sms', 'health', 'index',
                                     'public.about', 'public.privacy', 'plans.index')
        ):
            return None
        token = _session.get('user_session_token')
        if not token:
            return None
        from app.models import UserSession
        from datetime import datetime, timezone
        user_session = UserSession.query.filter_by(
            session_token=token, user_id=_cu.id, is_active=True
        ).first()
        if not user_session:
            _lu()
            from flask import flash, redirect, url_for
            flash('Sua sessão foi encerrada. Faça login novamente.', 'warning')
            return redirect(url_for('auth.login'))
        # Update last activity
        user_session.last_activity_at = datetime.now(timezone.utc)
        from app.extensions import db
        db.session.commit()
        return None
    
    # Root route — home page for guests, dashboard for authenticated users
    from flask import render_template, jsonify, redirect, url_for

    @app.route("/")
    def index():
        from flask_login import current_user as _index_user
        if _index_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        return render_template("public/index.html")

    @app.route("/health")
    def health():
        """Health check endpoint for load balancers and Docker healthchecks."""
        import time
        from flask import current_app as _app

        checks = {
            "status": "ok",
            "db": False,
            "redis": False,
            "s3": None,
            "celery_worker": None,
            "celery_beat": None,
        }

        # Check PostgreSQL
        try:
            db.session.execute(db.text("SELECT 1"))
            checks["db"] = True
        except Exception:
            checks["status"] = "degraded"

        # Check Redis
        redis_client = None
        try:
            from app.redis_client import get_redis_client
            redis_client = get_redis_client()
            if redis_client:
                redis_client.set("healthcheck", "ok", ex=10)
                if redis_client.get("healthcheck") == b"ok":
                    checks["redis"] = True
                else:
                    checks["redis"] = False
                    checks["status"] = "degraded"
            else:
                checks["redis"] = None  # Redis not configured / unavailable
        except Exception:
            checks["redis"] = False
            checks["status"] = "degraded"

        # Check S3
        try:
            storage = getattr(_app, "photo_storage", None)
            if storage and hasattr(storage, "health_check"):
                checks["s3"] = storage.health_check()
                if checks["s3"] is False:
                    checks["status"] = "degraded"
            else:
                checks["s3"] = None  # S3 not configured
        except Exception:
            checks["s3"] = False
            checks["status"] = "degraded"

        # Check Celery heartbeat(s)
        if redis_client:
            try:
                now = time.time()

                def _fresh_enough(key: str, max_age_seconds: int = 300):
                    raw = redis_client.get(key)
                    if not raw:
                        return False
                    try:
                        ts = float(raw.decode() if isinstance(raw, bytes) else raw)
                        return (now - ts) < max_age_seconds
                    except Exception:
                        return False

                checks["celery_worker"] = _fresh_enough("celery:worker:heartbeat")
                checks["celery_beat"] = _fresh_enough("celery:beat:heartbeat")

                # Only degrade if both are down (more forgiving for MVP)
                if checks["celery_worker"] is False and checks["celery_beat"] is False:
                    checks["status"] = "degraded"

            except Exception:
                checks["celery_worker"] = False
                checks["celery_beat"] = False
                checks["status"] = "degraded"

        status_code = 200 if checks["status"] == "ok" else 503
        return jsonify(checks), status_code

    # Security headers on every response
    app.after_request(add_security_headers)

    # HTTPS redirect middleware
    app.wsgi_app = HTTPSRedirectMiddleware(
        app.wsgi_app,
        force_https=app.config.get("FORCE_HTTPS", False),
    )

    # Request-ID tracking middleware
    app.wsgi_app = RequestIDMiddleware(app.wsgi_app)

    # Prometheus metrics (optional — no-op if package not installed)
    from app.monitoring import init_metrics
    init_metrics(app)

    # Structured JSON logging in production
    from app.logging_config import configure_logging
    configure_logging(app)

    # Photo storage backend (local or S3, based on STORAGE_BACKEND config)
    from app.storage import get_photo_storage

    app.photo_storage = get_photo_storage(app)

    # Custom error pages
    register_error_handlers(app)

    # CLI
    register_cli(app)

    return app
