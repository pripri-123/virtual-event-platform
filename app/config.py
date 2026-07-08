"""Application configuration classes.

Flask loads one of these configs based on FLASK_ENV.
Secrets and connection strings always come from environment variables,
never hard-coded in source files.
"""

import os
from pathlib import Path

# Project root: virtual-event-platform/
BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"


def _resolve_database_uri() -> str:
    """Build SQLAlchemy URI — SQLite locally, Azure SQL in production."""
    uri = os.environ.get("DATABASE_URL", "")

    # Build from Azure SQL components if provided (production)
    azure_server = os.environ.get("AZURE_SQL_SERVER", "")
    azure_db = os.environ.get("AZURE_SQL_DATABASE", "")
    azure_user = os.environ.get("AZURE_SQL_USERNAME", "")
    azure_password = os.environ.get("AZURE_SQL_PASSWORD", "")
    if azure_server and azure_db and azure_user and azure_password:
        from app.utils import build_azure_sql_uri

        return build_azure_sql_uri(azure_server, azure_db, azure_user, azure_password)

    if not uri or uri.startswith("sqlite:///instance/"):
        db_path = (INSTANCE_DIR / "vehp.db").resolve().as_posix()
        return f"sqlite:///{db_path}"
    return uri


class Config:
    """Base configuration shared by all environments."""

    # Required for signing session cookies — must be set in production
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")

    # SQLAlchemy settings
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _resolve_database_uri()

    # Flask-WTF CSRF
    WTF_CSRF_ENABLED = True

    # Session cookie security (enabled in production)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 60 * 60 * 24 * 30  # 30 days

    # Pagination default for list views (Phase 7)
    EVENTS_PER_PAGE = 10

    # Azure Blob Storage (Phase 11)
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get("AZURE_STORAGE_CONNECTION_STRING", "")
    AZURE_STORAGE_CONTAINER = os.environ.get("AZURE_STORAGE_CONTAINER", "vehp-uploads")

    # Azure Functions (Phase 13)
    FUNCTION_APP_URL = os.environ.get("FUNCTION_APP_URL", "")
    FUNCTION_APP_KEY = os.environ.get("FUNCTION_APP_KEY", "")

    # Application Insights (Phase 14)
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get(
        "APPLICATIONINSIGHTS_CONNECTION_STRING", ""
    )


class DevelopmentConfig(Config):
    """Local development — debug on, relaxed cookies."""

    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False


class ProductionConfig(Config):
    """Azure App Service — debug off, secure cookies over HTTPS."""

    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

    # Fail fast if secret is missing in production
    @classmethod
    def init_app(cls, app):  # type: ignore[no-untyped-def]
        if app.config["SECRET_KEY"] == "dev-only-change-me":
            raise ValueError("SECRET_KEY environment variable must be set in production.")


class TestingConfig(Config):
    """In-memory SQLite for automated tests (Phase 19)."""

    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


# Map FLASK_ENV values to config classes
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
