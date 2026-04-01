# app/plans_page/__init__.py
from flask import Blueprint

plans_page_bp = Blueprint("plans", __name__, url_prefix="/plans")

from app.plans_page import routes  # noqa: E402, F401
