"""Event registration for attendees."""

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Event, EventStatus, Registration, RegistrationStatus, utcnow
from app.services.notification_service import (
    notify_new_registration,
    notify_registration_cancelled,
    notify_registration_confirmed,
)
from app.utils import participant_required

registrations_bp = Blueprint("registrations", __name__, url_prefix="/registrations")


def _get_published_event(event_id: int) -> Event:
    event = db.session.get(Event, event_id)
    if event is None or event.status != EventStatus.PUBLISHED:
        abort(404)
    return event


@registrations_bp.route("/my")
@participant_required
def my_registrations():
    """List events the participant is registered for."""
    registrations = (
        Registration.query.filter_by(user_id=current_user.id, status=RegistrationStatus.CONFIRMED)
        .join(Event)
        .order_by(Event.start_datetime.asc())
        .all()
    )
    return render_template("registrations/my.html", registrations=registrations)


@registrations_bp.route("/<int:event_id>/register", methods=["POST"])
@login_required
def register(event_id: int):
    """Register the current user for a published event."""
    if current_user.role_name != "participant":
        flash("Only participants can register for events.", "warning")
        return redirect(url_for("events.detail", event_id=event_id))

    event = _get_published_event(event_id)

    existing = Registration.query.filter_by(user_id=current_user.id, event_id=event_id).first()
    if existing and existing.status == RegistrationStatus.CONFIRMED:
        flash("You are already registered for this event.", "info")
        return redirect(url_for("events.detail", event_id=event_id))

    if event.seats_available <= 0:
        flash("Sorry, this event is full.", "warning")
        return redirect(url_for("events.detail", event_id=event_id))

    if existing:
        existing.status = RegistrationStatus.CONFIRMED
        existing.registered_at = utcnow()
        registration = existing
    else:
        registration = Registration(user_id=current_user.id, event_id=event_id)
        db.session.add(registration)

    db.session.flush()
    notify_registration_confirmed(current_user.id, event.title, registration.confirmation_code)
    notify_new_registration(event.organizer_id, current_user.full_name, event.title)
    db.session.commit()
    flash(f"You are registered for '{event.title}'!", "success")
    return redirect(url_for("events.detail", event_id=event_id))


@registrations_bp.route("/<int:event_id>/cancel", methods=["POST"])
@participant_required
def cancel(event_id: int):
    """Cancel registration for an event."""
    registration = Registration.query.filter_by(
        user_id=current_user.id,
        event_id=event_id,
        status=RegistrationStatus.CONFIRMED,
    ).first()

    if registration is None:
        flash("You are not registered for this event.", "warning")
        return redirect(url_for("events.detail", event_id=event_id))

    event = registration.event
    registration.status = RegistrationStatus.CANCELLED
    notify_registration_cancelled(current_user.id, event.title)
    db.session.commit()

    flash(f"Registration cancelled for '{event.title}'.", "info")
    return redirect(url_for("registrations.my_registrations"))
