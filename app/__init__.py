import logging
from flask import Flask
from config import Config
from app.extensions import db, login_manager, csrf, limiter
from app.models import PoliceUser
from app.sessions.expiry import start_expiry_daemon
from app.cli import register_cli

logger = logging.getLogger(__name__)

_DEFAULT_SECRET_KEY = "dev-secret-change-in-prod"

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    if app.config.get("SECRET_KEY") == _DEFAULT_SECRET_KEY:
        logger.warning(
            "Using default SECRET_KEY. Set the SECRET_KEY environment variable "
            "before deploying to production."
        )
    
    # Extensions
    db.init_app(app)
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
    from flask import redirect, url_for
    @app.route("/")
    def index():
        return redirect(url_for("auth.login"))
    
    # DB setup
    with app.app_context():
        db.create_all()
    
    # CLI
    register_cli(app)
    
    # Start expiry daemon
    start_expiry_daemon(app)
    
    return app
