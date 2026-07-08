"""Analytics queries for dashboard charts — works on SQLite and Azure SQL."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func

from app.extensions import db
from app.models import Event, EventStatus, Registration, RegistrationStatus, Role, User


def _date_label(value: datetime | str) -> str:
    """Normalize a date value to a short display label."""
    if isinstance(value, str):
        return value[:10]
    return value.strftime("%b %d")


def _series_from_rows(rows: list[tuple[Any, int]], fill_days: int = 30) -> dict[str, list]:
    """Build Chart.js labels + data arrays, filling missing days with zero."""
    end = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = end - timedelta(days=fill_days - 1)
    counts: dict[str, int] = {}
    for day_value, count in rows:
        if isinstance(day_value, datetime):
            key = day_value.strftime("%Y-%m-%d")
        else:
            key = str(day_value)[:10]
        counts[key] = count

    labels: list[str] = []
    data: list[int] = []
    current = start
    while current <= end:
        key = current.strftime("%Y-%m-%d")
        labels.append(_date_label(current))
        data.append(counts.get(key, 0))
        current += timedelta(days=1)
    return {"labels": labels, "data": data}


def get_registration_trend(days: int = 30, organizer_id: int | None = None) -> dict[str, list]:
    """Daily confirmed registrations over the last N days."""
    since = datetime.now() - timedelta(days=days)
    day_col = func.date(Registration.registered_at)

    query = (
        db.session.query(day_col, func.count(Registration.id))
        .filter(
            Registration.status == RegistrationStatus.CONFIRMED,
            Registration.registered_at >= since,
        )
    )
    if organizer_id is not None:
        query = query.join(Event).filter(Event.organizer_id == organizer_id)

    rows = query.group_by(day_col).order_by(day_col).all()
    return _series_from_rows(rows, fill_days=days)


def get_events_by_status(organizer_id: int | None = None) -> dict[str, list]:
    """Count events grouped by status."""
    query = db.session.query(Event.status, func.count(Event.id))
    if organizer_id is not None:
        query = query.filter(Event.organizer_id == organizer_id)
    rows = query.group_by(Event.status).all()

    labels = [status.value.title() for status, _ in rows]
    data = [count for _, count in rows]
    return {"labels": labels, "data": data}


def get_users_by_role() -> dict[str, list]:
    """Count users grouped by role (admin dashboard)."""
    rows = (
        db.session.query(Role.name, func.count(User.id))
        .join(User, User.role_id == Role.id)
        .group_by(Role.name)
        .order_by(Role.name)
        .all()
    )
    return {
        "labels": [name.title() for name, _ in rows],
        "data": [count for _, count in rows],
    }


def get_events_by_category(organizer_id: int | None = None) -> dict[str, list]:
    """Count events grouped by category."""
    query = (
        db.session.query(Event.category, func.count(Event.id))
        .filter(Event.category.isnot(None), Event.category != "")
    )
    if organizer_id is not None:
        query = query.filter(Event.organizer_id == organizer_id)

    rows = query.group_by(Event.category).order_by(func.count(Event.id).desc()).limit(8).all()
    return {
        "labels": [cat or "Uncategorized" for cat, _ in rows],
        "data": [count for _, count in rows],
    }


def get_registrations_by_event(organizer_id: int, limit: int = 8) -> dict[str, list]:
    """Top events by confirmed registration count for an organizer."""
    rows = (
        db.session.query(Event.title, func.count(Registration.id))
        .join(Registration, Registration.event_id == Event.id)
        .filter(
            Event.organizer_id == organizer_id,
            Registration.status == RegistrationStatus.CONFIRMED,
        )
        .group_by(Event.id, Event.title)
        .order_by(func.count(Registration.id).desc())
        .limit(limit)
        .all()
    )
    return {
        "labels": [title[:30] + ("…" if len(title) > 30 else "") for title, _ in rows],
        "data": [count for _, count in rows],
    }


def get_participant_category_breakdown(user_id: int) -> dict[str, list]:
    """Categories of events a participant is registered for."""
    rows = (
        db.session.query(Event.category, func.count(Registration.id))
        .join(Event, Registration.event_id == Event.id)
        .filter(
            Registration.user_id == user_id,
            Registration.status == RegistrationStatus.CONFIRMED,
            Event.category.isnot(None),
            Event.category != "",
        )
        .group_by(Event.category)
        .all()
    )
    return {
        "labels": [cat or "Other" for cat, _ in rows],
        "data": [count for _, count in rows],
    }


def get_admin_analytics() -> dict[str, dict[str, list]]:
    """All chart datasets for the admin dashboard."""
    return {
        "registration_trend": get_registration_trend(),
        "events_by_status": get_events_by_status(),
        "users_by_role": get_users_by_role(),
        "events_by_category": get_events_by_category(),
    }


def get_organizer_analytics(organizer_id: int) -> dict[str, dict[str, list]]:
    """All chart datasets for the organizer dashboard."""
    return {
        "registration_trend": get_registration_trend(organizer_id=organizer_id),
        "events_by_status": get_events_by_status(organizer_id=organizer_id),
        "registrations_by_event": get_registrations_by_event(organizer_id),
        "events_by_category": get_events_by_category(organizer_id=organizer_id),
    }


def get_participant_analytics(user_id: int) -> dict[str, dict[str, list]]:
    """Chart datasets for the participant dashboard."""
    return {
        "category_breakdown": get_participant_category_breakdown(user_id),
    }
