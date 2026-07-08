"""Event management — create, browse, edit, and delete events."""

from datetime import datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.forms import EventForm
from app.models import Event, EventStatus, Registration, RegistrationStatus
from app.utils import organizer_required, parse_datetime_local

events_bp = Blueprint("events", __name__, url_prefix="/events")


def _get_event_or_404(event_id: int) -> Event:
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)
    return event


def _can_manage_event(event: Event) -> bool:
    """True if current user is the organizer or an admin."""
    if not current_user.is_authenticated:
        return False
    return current_user.role_name == "admin" or event.organizer_id == current_user.id


def _can_view_event(event: Event) -> bool:
    """Published events are public; drafts only for owner/admin."""
    if event.status == EventStatus.PUBLISHED:
        return True
    return _can_manage_event(event)


def _populate_event_from_form(event: Event, form: EventForm) -> None:
    """Apply validated form data to an Event instance."""
    try:
        start = parse_datetime_local(form.start_datetime.data)
        end = parse_datetime_local(form.end_datetime.data)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc

    if end <= start:
        raise ValueError("End date must be after start date.")

    event.title = form.title.data.strip()
    event.description = form.description.data.strip() if form.description.data else None
    event.category = form.category.data
    event.start_datetime = start
    event.end_datetime = end
    event.max_capacity = form.max_capacity.data
    event.status = EventStatus(form.status.data)
    event.updated_at = datetime.now()


def _user_registration(event_id: int):
    if not current_user.is_authenticated:
        return None
    return Registration.query.filter_by(
        user_id=current_user.id,
        event_id=event_id,
        status=RegistrationStatus.CONFIRMED,
    ).first()


@events_bp.route("/")
def list_events():
    """Browse published events with search, filter, and pagination."""
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "", type=str).strip()
    category = request.args.get("category", "", type=str).strip()
    per_page = current_app.config["EVENTS_PER_PAGE"]

    query = Event.query.filter(Event.status == EventStatus.PUBLISHED)

    if search:
        like = f"%{search}%"
        query = query.filter(or_(Event.title.ilike(like), Event.description.ilike(like)))

    if category:
        query = query.filter(Event.category == category)

    pagination = query.order_by(Event.start_datetime.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template(
        "events/list.html",
        events=pagination.items,
        pagination=pagination,
        search=search,
        category=category,
    )


@events_bp.route("/my")
@organizer_required
def my_events():
    """Organizer view of their own events."""
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["EVENTS_PER_PAGE"]

    pagination = (
        Event.query.filter_by(organizer_id=current_user.id)
        .order_by(Event.start_datetime.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )

    return render_template("events/my_events.html", events=pagination.items, pagination=pagination)


@events_bp.route("/create", methods=["GET", "POST"])
@organizer_required
def create():
    """Create a new event."""
    form = EventForm()
    if form.validate_on_submit():
        try:
            event = Event(organizer_id=current_user.id)
            _populate_event_from_form(event, form)
            db.session.add(event)
            db.session.commit()
            flash(f"Event '{event.title}' created successfully.", "success")
            return redirect(url_for("events.detail", event_id=event.id))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("events/form.html", form=form, title="Create Event")


@events_bp.route("/<int:event_id>")
def detail(event_id: int):
    """Event detail page with registration status and Q&A link."""
    event = _get_event_or_404(event_id)
    if not _can_view_event(event):
        abort(403)

    registration = _user_registration(event_id)
    question_count = event.chat_messages.filter_by(is_question=True).count()

    return render_template(
        "events/detail.html",
        event=event,
        registration=registration,
        can_manage=_can_manage_event(event),
        question_count=question_count,
    )


@events_bp.route("/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def edit(event_id: int):
    """Edit an existing event (owner or admin only)."""
    event = _get_event_or_404(event_id)
    if not _can_manage_event(event):
        abort(403)

    form = EventForm(obj=event)
    if request.method == "GET":
        form.start_datetime.data = event.start_datetime.strftime("%Y-%m-%dT%H:%M")
        form.end_datetime.data = event.end_datetime.strftime("%Y-%m-%dT%H:%M")
        form.status.data = event.status.value

    if form.validate_on_submit():
        try:
            _populate_event_from_form(event, form)
            db.session.commit()
            flash(f"Event '{event.title}' updated.", "success")
            return redirect(url_for("events.detail", event_id=event.id))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("events/form.html", form=form, title="Edit Event", event=event)


@events_bp.route("/<int:event_id>/delete", methods=["POST"])
@login_required
def delete(event_id: int):
    """Delete an event (owner or admin only)."""
    event = _get_event_or_404(event_id)
    if not _can_manage_event(event):
        abort(403)

    title = event.title
    db.session.delete(event)
    db.session.commit()
    flash(f"Event '{title}' deleted.", "info")
    return redirect(url_for("events.my_events"))
