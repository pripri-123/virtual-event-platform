"""Register all Flask blueprints with the application.

Keeping registration in one file makes it easy to see every URL namespace
at a glance. Individual route logic lives inside each blueprint module.
"""

from flask import Flask

from app.blueprints.auth import auth_bp
from app.blueprints.dashboard import dashboard_bp
from app.blueprints.events import events_bp
from app.blueprints.main import main_bp
from app.blueprints.notifications import notifications_bp
from app.blueprints.qa import qa_bp
from app.blueprints.registrations import registrations_bp


def register_blueprints(app: Flask) -> None:
    """Attach all blueprints to the Flask app instance."""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(registrations_bp)
    app.register_blueprint(qa_bp)
    app.register_blueprint(notifications_bp)
