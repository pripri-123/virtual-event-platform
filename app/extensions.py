"""Shared Flask extensions.

Extensions are created here without binding them to the app immediately.
This avoids circular imports: models can import `db` without importing the app.
Each extension is initialized inside `create_app()` in app/__init__.py.
"""

from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Database ORM — maps Python classes to SQL tables
db = SQLAlchemy()

# Alembic-powered schema migrations
migrate = Migrate()

# Session-based authentication (login/logout/remember-me)
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "warning"

# Cross-Site Request Forgery protection for all POST forms
csrf = CSRFProtect()
