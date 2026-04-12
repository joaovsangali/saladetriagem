from flask import render_template
from app.public import public_bp


@public_bp.route("/sobre")
def about():
    return render_template("public/about.html")


@public_bp.route("/privacidade")
def privacy():
    return render_template("public/privacy.html")
