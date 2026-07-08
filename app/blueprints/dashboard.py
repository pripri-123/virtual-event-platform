"""Dashboard blueprint — role-based landing pages with live statistics."""

from datetime import datetime

from flask import Blueprint, redirect, render_template
from flask_login import current_user, login_required

from app.models import Event, EventStatus, Notification, Registration, RegistrationStatus, User
from app.services.analytics_service import (
    get_admin_analytics,
    get_organizer_analytics,
    get_participant_analytics,
)
from app.services.notification_service import get_unread_count
from app.utils import admin_required, get_dashboard_url_for_role, organizer_required, participant_required

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    """Redirect to the dashboard matching the user's role."""
    return redirect(get_dashboard_url_for_role(current_user.role_name))


@dashboard_bp.route("/admin")
@admin_required
def admin():
    """Admin overview of platform activity."""
    stats = {
        "users": User.query.count(),
        "events": Event.query.count(),
        "published_events": Event.query.filter_by(status=EventStatus.PUBLISHED).count(),
        "registrations": Registration.query.filter_by(status=RegistrationStatus.CONFIRMED).count(),
    }
    recent_events = Event.query.order_by(Event.created_at.desc()).limit(5).all()
    analytics = get_admin_analytics()
    return render_template(
        "dashboard/admin.html", stats=stats, recent_events=recent_events, analytics=analytics
    )


@dashboard_bp.route("/organizer")
@organizer_required
def organizer():
    """Organizer overview of their events and registrations."""
    base_query = Event.query.filter_by(organizer_id=current_user.id)
    event_ids = [row[0] for row in base_query.with_entities(Event.id).all()]
    now = datetime.now()

    total_registrations = 0
    if event_ids:
        total_registrations = Registration.query.filter(
            Registration.event_id.in_(event_ids),
            Registration.status == RegistrationStatus.CONFIRMED,
        ).count()

    stats = {
        "total_events": base_query.count(),
        "published_events": base_query.filter_by(status=EventStatus.PUBLISHED).count(),
        "total_registrations": total_registrations,
        "upcoming_events": base_query.filter(Event.start_datetime >= now).count(),
    }
    recent_events = base_query.order_by(Event.start_datetime.asc()).limit(5).all()
    analytics = get_organizer_analytics(current_user.id)
    return render_template(
        "dashboard/organizer.html",
        stats=stats,
        recent_events=recent_events,
        analytics=analytics,
    )


@dashboard_bp.route("/participant")
@participant_required
def participant():
    """Participant overview of registrations and notifications."""
    registrations = (
        Registration.query.filter_by(user_id=current_user.id, status=RegistrationStatus.CONFIRMED)
        .join(Event)
        .order_by(Event.start_datetime.asc())
    )
    now = datetime.now()
    stats = {
        "registered_events": registrations.count(),
        "upcoming_events": registrations.filter(Event.start_datetime >= now).count(),
        "unread_notifications": get_unread_count(current_user.id),
    }
    upcoming = registrations.limit(5).all()
    recent_notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(5)
        .all()
    )
    analytics = get_participant_analytics(current_user.id)
    return render_template(
        "dashboard/participant.html",
        stats=stats,
        upcoming=upcoming,
        recent_notifications=recent_notifications,
        analytics=analytics,
    )
