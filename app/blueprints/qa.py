"""Q&A for registered event attendees."""

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.forms import QuestionForm
from app.models import ChatMessage, Event, EventStatus, Registration, RegistrationStatus

qa_bp = Blueprint("qa", __name__, url_prefix="/events")


def _can_access_qa(event: Event) -> bool:
    """Organizer or confirmed registrant can access Q&A."""
    if not current_user.is_authenticated:
        return False
    if current_user.role_name == "admin":
        return True
    if event.organizer_id == current_user.id:
        return True
    return (
        Registration.query.filter_by(
            user_id=current_user.id,
            event_id=event.id,
            status=RegistrationStatus.CONFIRMED,
        ).first()
        is not None
    )


@qa_bp.route("/<int:event_id>/qa", methods=["GET", "POST"])
@login_required
def event_qa(event_id: int):
    """View and post Q&A questions for an event."""
    event = db.session.get(Event, event_id)
    if event is None:
        abort(404)

    if event.status not in (EventStatus.PUBLISHED, EventStatus.COMPLETED):
        abort(403)

    if not _can_access_qa(event):
        flash("Register for this event to join the Q&A.", "warning")
        return redirect(url_for("events.detail", event_id=event_id))

    form = QuestionForm()
    if form.validate_on_submit():
        message = ChatMessage(
            event_id=event.id,
            user_id=current_user.id,
            message=form.message.data.strip(),
            is_question=True,
        )
        db.session.add(message)
        db.session.commit()
        flash("Your question has been posted.", "success")
        return redirect(url_for("qa.event_qa", event_id=event_id))

    questions = (
        ChatMessage.query.filter_by(event_id=event_id, is_question=True)
        .order_by(ChatMessage.sent_at.desc())
        .all()
    )

    is_organizer = event.organizer_id == current_user.id

    return render_template(
        "qa/event_qa.html",
        event=event,
        form=form,
        questions=questions,
        is_organizer=is_organizer,
    )
