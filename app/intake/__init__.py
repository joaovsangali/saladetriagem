from flask import Blueprint
intake_bp = Blueprint("intake", __name__)
from app.intake import routes  # noqa
