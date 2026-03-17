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
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(intake_bp)
    
    # Root redirect
    from flask import jsonify, redirect, url_for

    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))

    @app.route("/health")
    def health():
        """Health check endpoint for load balancers and Docker healthchecks."""
        try:
            db.session.execute(db.text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
        status = "ok" if db_ok else "degraded"
        return jsonify({"status": status, "db": db_ok}), 200 if db_ok else 503

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

    # Custom error pages
    register_error_handlers(app)

    # CLI
    register_cli(app)

    return app
