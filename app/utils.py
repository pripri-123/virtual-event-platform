"""Shared utility functions and decorators."""

from __future__ import annotations

from datetime import datetime
from functools import wraps
from typing import Any, Callable
from urllib.parse import quote_plus

from flask import abort, flash, redirect, url_for
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash


def format_datetime(value: datetime | None, fmt: str = "%b %d, %Y %H:%M") -> str:
    """Format a datetime for display in templates."""
    if value is None:
        return "—"
    return value.strftime(fmt)


def hash_password(plain_password: str) -> str:
    """Hash a plain-text password for storage."""
    return generate_password_hash(plain_password)


def verify_password(password_hash: str, plain_password: str) -> bool:
    """Verify a plain-text password against its hash."""
    return check_password_hash(password_hash, plain_password)


def role_required(*roles: str) -> Callable:
    """Restrict a route to authenticated users with one of the given roles.

    Usage:
        @role_required("admin")
        @role_required("admin", "organizer")
    """

    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        @login_required
        def wrapped_view(*args: Any, **kwargs: Any):
            if current_user.role_name not in roles:
                flash("You do not have permission to access that page.", "danger")
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def admin_required(view_func: Callable) -> Callable:
    """Shortcut decorator for admin-only routes."""
    return role_required("admin")(view_func)


def organizer_required(view_func: Callable) -> Callable:
    """Shortcut decorator for organizer-only routes."""
    return role_required("organizer")(view_func)


def participant_required(view_func: Callable) -> Callable:
    """Shortcut decorator for participant-only routes."""
    return role_required("participant")(view_func)


def get_dashboard_url_for_role(role_name: str) -> str:
    """Return the dashboard URL for a given role name."""
    mapping = {
        "admin": "dashboard.admin",
        "organizer": "dashboard.organizer",
        "participant": "dashboard.participant",
    }
    endpoint = mapping.get(role_name, "main.index")
    return url_for(endpoint)


def parse_datetime_local(value: str) -> datetime:
    """Parse HTML datetime-local input (YYYY-MM-DDTHH:MM) to datetime."""
    if not value:
        raise ValueError("Datetime is required.")
    return datetime.fromisoformat(value)


def build_azure_sql_uri(
    server: str,
    database: str,
    username: str,
    password: str,
    driver: str = "ODBC Driver 18 for SQL Server",
) -> str:
    """Build SQLAlchemy URI for Azure SQL Database."""
    host = server.strip()
    if host.endswith(".database.windows.net"):
        host = host[: -len(".database.windows.net")]
    encoded_password = quote_plus(password)
    encoded_driver = quote_plus(driver)
    return (
        f"mssql+pyodbc://{username}:{encoded_password}"
        f"@{host}.database.windows.net:1433/{database}"
        f"?driver={encoded_driver}&Encrypt=yes&TrustServerCertificate=no"
    )

