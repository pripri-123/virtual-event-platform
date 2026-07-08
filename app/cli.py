"""Flask CLI commands for database seeding and maintenance."""

from datetime import datetime, timedelta

import click
from flask.cli import with_appcontext
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Event, EventStatus, Role, User, seed_roles


def register_commands(app):
    """Register custom Flask CLI commands on the application."""

    @app.cli.command("seed-roles")
    @with_appcontext
    def seed_roles_command():
        """Insert default roles (admin, organizer, participant)."""
        seed_roles()
        click.echo("Default roles seeded successfully.")

    @app.cli.command("seed-admin")
    @click.option("--email", default="admin@vehp.com", help="Admin email address")
    @click.option("--password", default="Admin@123", help="Admin password")
    @click.option("--name", default="System Admin", help="Admin display name")
    @with_appcontext
    def seed_admin_command(email, password, name):
        """Create an admin user (for development only)."""
        seed_roles()
        admin_role = Role.query.filter_by(name="admin").first()
        if User.query.filter_by(email=email).first():
            click.echo(f"User {email} already exists.")
            return
        admin = User(
            role_id=admin_role.id,
            email=email,
            password_hash=generate_password_hash(password),
            full_name=name,
            is_active=True,
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Admin user created: {email}")

    @app.cli.command("init-db")
    @with_appcontext
    def init_db_command():
        """Seed roles and print table counts (after migrations)."""
        seed_roles()
        roles = Role.query.count()
        click.echo(f"Database ready. Roles: {roles}")

    @app.cli.command("db-check-azure")
    @with_appcontext
    def db_check_azure_command():
        """Test connectivity to Azure SQL Database."""
        uri = db.engine.url
        if uri.drivername != "mssql+pyodbc":
            click.echo(
                "Not using Azure SQL. Set AZURE_SQL_SERVER, AZURE_SQL_DATABASE, "
                "AZURE_SQL_USERNAME, and AZURE_SQL_PASSWORD in .env."
            )
            raise SystemExit(1)

        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT 1 AS ok"))
                row = result.fetchone()
            click.echo(f"Connected to Azure SQL: {uri.host}/{uri.database}")
            click.echo(f"Query test: SELECT 1 => {row[0]}")
        except Exception as exc:
            click.echo(f"Connection failed: {exc}", err=True)
            raise SystemExit(1) from exc

    @app.cli.command("seed-demo")
    @with_appcontext
    def seed_demo_command():
        """Create demo users and a sample published event."""
        seed_roles()
        organizer_role = Role.query.filter_by(name="organizer").first()
        participant_role = Role.query.filter_by(name="participant").first()

        organizer = User.query.filter_by(email="organizer@vehp.com").first()
        if not organizer:
            organizer = User(
                role_id=organizer_role.id,
                email="organizer@vehp.com",
                password_hash=generate_password_hash("Organizer@123"),
                full_name="Demo Organizer",
            )
            db.session.add(organizer)
            db.session.flush()

        if not User.query.filter_by(email="participant@vehp.com").first():
            db.session.add(
                User(
                    role_id=participant_role.id,
                    email="participant@vehp.com",
                    password_hash=generate_password_hash("Participant@123"),
                    full_name="Demo Participant",
                )
            )

        if not Event.query.filter_by(title="Cloud Computing Summit 2026").first():
            start = datetime.now() + timedelta(days=14)
            end = start + timedelta(hours=3)
            db.session.add(
                Event(
                    organizer_id=organizer.id,
                    title="Cloud Computing Summit 2026",
                    description="A demo virtual event covering Azure, Flask, and cloud architecture basics.",
                    category="conference",
                    start_datetime=start,
                    end_datetime=end,
                    max_capacity=50,
                    status=EventStatus.PUBLISHED,
                )
            )

        db.session.commit()
        click.echo("Demo data ready:")
        click.echo("  Organizer: organizer@vehp.com / Organizer@123")
        click.echo("  Participant: participant@vehp.com / Participant@123")
