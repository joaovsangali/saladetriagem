import click
from flask.cli import with_appcontext
from app.extensions import db
from app.models import PoliceUser

def register_cli(app):
    @app.cli.command("create-user")
    @click.option("--email", required=True, help="User email")
    @click.option("--password", required=True, help="User password")
    @click.option("--name", required=True, help="Display name")
    @with_appcontext
    def create_user(email, password, name):
        """Create a police user."""
        if PoliceUser.query.filter_by(email=email.lower()).first():
            click.echo(f"User {email} already exists.")
            return
        u = PoliceUser(email=email.lower(), display_name=name, email_confirmed=True)
        u.set_password(password)
        db.session.add(u)
        db.session.commit()
        click.echo(f"User '{name}' <{email}> created (id={u.id}).")
