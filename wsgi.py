"""WSGI entry point for production deployment with Gunicorn."""

import os
from app import create_app
from config import Config, ProductionConfig

env = os.environ.get("FLASK_ENV", "development")
config_class = ProductionConfig if env == "production" else Config

app = create_app(config_class)

if __name__ == "__main__":
    app.run()
