"""Application factory.

This module is the heart of the Flask app (equivalent to a root-level app.py).
Using a factory function instead of a global `app` object allows:
  - Multiple configs (dev / test / production)
  - Cleaner testing
  - No circular import problems
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template

from app.config import config_by_name
from app.extensions import csrf, db, login_manager, migrate
from app.routes import register_blueprints


def create_app(config_name: str | None = None) -> Flask:
    """Create and configure the Flask application."""
    # Load .env from project root before reading os.environ
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    config_class = config_by_name[config_name]
    app.config.from_object(config_class)

    if hasattr(config_class, "init_app"):
        config_class.init_app(app)

    # Ensure instance/ folder exists for SQLite database file
    instance_path = Path(app.instance_path)
    instance_path.mkdir(parents=True, exist_ok=True)

    # Initialize extensions with this app instance
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Jinja2 template helpers
    from app.utils import format_datetime

    app.jinja_env.filters["format_datetime"] = format_datetime

    # Import models so SQLAlchemy metadata is registered for migrations
    from app import models  # noqa: F401

    # Flask-Login user loader
    @login_manager.user_loader
    def load_user(user_id: str):
        from app.models import User

        return db.session.get(User, int(user_id))

    # Azure Application Insights (optional — enabled when connection string is set)
    from app.services.telemetry_service import init_telemetry

    init_telemetry(app)

    # Register URL blueprints
    register_blueprints(app)

    # Register CLI commands (seed-roles, seed-admin, init-db)
    from app.cli import register_commands

    register_commands(app)

    @app.context_processor
    def inject_notifications():
        """Make unread notification count available in all templates."""
        from flask_login import current_user

        from app.services.notification_service import get_unread_count

        if current_user.is_authenticated:
            return {"unread_notification_count": get_unread_count(current_user.id)}
        return {"unread_notification_count": 0}

    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):  # noqa: ARG001
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):  # noqa: ARG001
        db.session.rollback()
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden(error):  # noqa: ARG001
        return render_template("errors/403.html"), 403

    return app
