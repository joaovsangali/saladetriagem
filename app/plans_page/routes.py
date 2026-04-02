# app/plans_page/routes.py
from flask import render_template
from flask_login import login_required, current_user
from app.plans_page import plans_page_bp
from app.plans import PLANS


@plans_page_bp.route("/")
@login_required
def index():
    return render_template("plans/index.html", plans=PLANS)
