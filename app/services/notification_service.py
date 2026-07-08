"""Notification helpers for in-app alerts."""

from app.extensions import db
from app.models import Notification


def create_notification(user_id: int, title: str, body: str) -> Notification:
    """Create and persist an in-app notification for a user."""
    notification = Notification(user_id=user_id, title=title, body=body, is_read=False)
    db.session.add(notification)
    return notification


def notify_registration_confirmed(user_id: int, event_title: str, confirmation_code: str) -> None:
    """Notify attendee that registration succeeded."""
    create_notification(
        user_id=user_id,
        title="Registration confirmed",
        body=f"You are registered for '{event_title}'. Confirmation code: {confirmation_code}",
    )


def notify_new_registration(organizer_id: int, attendee_name: str, event_title: str) -> None:
    """Notify organizer when someone registers for their event."""
    create_notification(
        user_id=organizer_id,
        title="New registration",
        body=f"{attendee_name} registered for your event '{event_title}'.",
    )


def notify_registration_cancelled(user_id: int, event_title: str) -> None:
    """Notify attendee that registration was cancelled."""
    create_notification(
        user_id=user_id,
        title="Registration cancelled",
        body=f"Your registration for '{event_title}' has been cancelled.",
    )


def get_unread_count(user_id: int) -> int:
    """Return count of unread notifications for a user."""
    return Notification.query.filter_by(user_id=user_id, is_read=False).count()
