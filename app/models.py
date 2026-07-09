"""SQLAlchemy database models for the Virtual Event Hosting Platform.

Normalized schema with 12 tables:
  Roles, Users, Events, Sessions, Registrations, Feedback,
  Polls, PollOptions, PollResponses, ChatMessages, Certificates, Notifications

All models inherit from `db.Model` and are registered when this module is imported.
"""

from __future__ import annotations

import enum
import secrets
import uuid
from datetime import datetime, timezone

from flask_login import UserMixin
from sqlalchemy import (
    CheckConstraint,
    Index,
    UniqueConstraint,
    event,
    update,
)
from sqlalchemy.orm import validates

from app.extensions import db


def utcnow() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------


class TimestampMixin:
    """Adds created_at column to any model."""

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EventStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class RegistrationStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    WAITLISTED = "waitlisted"


# ---------------------------------------------------------------------------
# Role
# ---------------------------------------------------------------------------


class Role(db.Model):
    """User role: admin, organizer, or participant."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)

    users = db.relationship("User", back_populates="role", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Role {self.name}>"


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------


class User(UserMixin, db.Model):
    """Platform user account."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    avatar_url = db.Column(db.String(512), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)

    role = db.relationship("Role", back_populates="users")
    organized_events = db.relationship(
        "Event", back_populates="organizer", lazy="dynamic", foreign_keys="Event.organizer_id"
    )
    registrations = db.relationship("Registration", back_populates="user", lazy="dynamic")
    feedback_entries = db.relationship("Feedback", back_populates="user", lazy="dynamic")
    poll_responses = db.relationship("PollResponse", back_populates="user", lazy="dynamic")
    chat_messages = db.relationship("ChatMessage", back_populates="user", lazy="dynamic")
    certificates = db.relationship("Certificate", back_populates="user", lazy="dynamic")
    notifications = db.relationship("Notification", back_populates="user", lazy="dynamic")

    @property
    def role_name(self) -> str:
        """Role name string used by @role_required decorator."""
        return self.role.name if self.role else ""

    def __repr__(self) -> str:
        return f"<User {self.email}>"


# ---------------------------------------------------------------------------
# Event
# ---------------------------------------------------------------------------


class Event(db.Model):
    """Virtual event created by an organizer."""

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("end_datetime > start_datetime", name="ck_event_datetime_order"),
        CheckConstraint("max_capacity >= 0", name="ck_event_capacity_nonneg"),
        Index("ix_events_status_start", "status", "start_datetime"),
        Index("ix_events_organizer", "organizer_id"),
        Index("ix_events_category", "category"),
    )

    id = db.Column(db.Integer, primary_key=True)
    organizer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    banner_url = db.Column(db.String(512), nullable=True)
    start_datetime = db.Column(db.DateTime, nullable=False, index=True)
    end_datetime = db.Column(db.DateTime, nullable=False)
    max_capacity = db.Column(db.Integer, default=100, nullable=False)
    status = db.Column(
        db.Enum(EventStatus),
        default=EventStatus.DRAFT,
        nullable=False,
        index=True,
    )
    category = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    organizer = db.relationship("User", back_populates="organized_events", foreign_keys=[organizer_id])
    sessions = db.relationship(
        "Session", back_populates="event", lazy="dynamic", cascade="all, delete-orphan"
    )
    registrations = db.relationship(
        "Registration", back_populates="event", lazy="dynamic", cascade="all, delete-orphan"
    )
    feedback_entries = db.relationship(
        "Feedback", back_populates="event", lazy="dynamic", cascade="all, delete-orphan"
    )
    polls = db.relationship("Poll", back_populates="event", lazy="dynamic", cascade="all, delete-orphan")
    chat_messages = db.relationship(
        "ChatMessage", back_populates="event", lazy="dynamic", cascade="all, delete-orphan"
    )
    certificates = db.relationship(
        "Certificate", back_populates="event", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def confirmed_registration_count(self) -> int:
        return self.registrations.filter_by(status=RegistrationStatus.CONFIRMED).count()

    @property
    def seats_available(self) -> int:
        return max(0, self.max_capacity - self.confirmed_registration_count)

    def __repr__(self) -> str:
        return f"<Event {self.title}>"


# ---------------------------------------------------------------------------
# Session
# ---------------------------------------------------------------------------


class Session(db.Model):
    """Agenda session within an event (talk, workshop, keynote)."""

    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("end_datetime > start_datetime", name="ck_session_datetime_order"),
        Index("ix_sessions_event_start", "event_id", "start_datetime"),
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    speaker_name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    meeting_link = db.Column(db.String(512), nullable=True)
    sort_order = db.Column(db.Integer, default=0, nullable=False)

    event = db.relationship("Event", back_populates="sessions")
    chat_messages = db.relationship("ChatMessage", back_populates="session", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Session {self.title}>"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


class Registration(db.Model):
    """Participant registration for an event."""

    __tablename__ = "registrations"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_registration_user_event"),
        Index("ix_registrations_event_status", "event_id", "status"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(
        db.Enum(RegistrationStatus),
        default=RegistrationStatus.CONFIRMED,
        nullable=False,
    )
    registered_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    confirmation_code = db.Column(
        db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )

    user = db.relationship("User", back_populates="registrations")
    event = db.relationship("Event", back_populates="registrations")

    def __repr__(self) -> str:
        return f"<Registration user={self.user_id} event={self.event_id}>"


# ---------------------------------------------------------------------------
# Feedback
# ---------------------------------------------------------------------------


class Feedback(db.Model):
    """Post-event feedback from a participant."""

    __tablename__ = "feedback"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_feedback_user_event"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_feedback_rating_range"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    submitted_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="feedback_entries")
    event = db.relationship("Event", back_populates="feedback_entries")

    @validates("rating")
    def validate_rating(self, _key: str, value: int) -> int:
        if value < 1 or value > 5:
            raise ValueError("Rating must be between 1 and 5.")
        return value

    def __repr__(self) -> str:
        return f"<Feedback event={self.event_id} rating={self.rating}>"


# ---------------------------------------------------------------------------
# Poll
# ---------------------------------------------------------------------------


class Poll(db.Model):
    """Live poll attached to an event."""

    __tablename__ = "polls"
    __table_args__ = (Index("ix_polls_event_active", "event_id", "is_active"),)

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    question = db.Column(db.String(500), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    event = db.relationship("Event", back_populates="polls")
    options = db.relationship(
        "PollOption", back_populates="poll", lazy="dynamic", cascade="all, delete-orphan"
    )
    responses = db.relationship(
        "PollResponse", back_populates="poll", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Poll {self.question[:30]}>"


class PollOption(db.Model):
    """Single answer choice for a poll."""

    __tablename__ = "poll_options"
    __table_args__ = (Index("ix_poll_options_poll", "poll_id"),)

    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    option_text = db.Column(db.String(255), nullable=False)
    vote_count = db.Column(db.Integer, default=0, nullable=False)

    poll = db.relationship("Poll", back_populates="options")
    responses = db.relationship("PollResponse", back_populates="poll_option", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<PollOption {self.option_text[:30]}>"


class PollResponse(db.Model):
    """One vote per user per poll."""

    __tablename__ = "poll_responses"
    __table_args__ = (
        UniqueConstraint("poll_id", "user_id", name="uq_poll_response_user"),
        Index("ix_poll_responses_poll", "poll_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("polls.id", ondelete="CASCADE"), nullable=False)
    poll_option_id = db.Column(
        db.Integer, db.ForeignKey("poll_options.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    responded_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    poll = db.relationship("Poll", back_populates="responses")
    poll_option = db.relationship("PollOption", back_populates="responses")
    user = db.relationship("User", back_populates="poll_responses")

    def __repr__(self) -> str:
        return f"<PollResponse poll={self.poll_id} user={self.user_id}>"


# ---------------------------------------------------------------------------
# ChatMessage
# ---------------------------------------------------------------------------


class ChatMessage(db.Model):
    """Live chat or Q&A message scoped to an event (optionally a session)."""

    __tablename__ = "chat_messages"
    __table_args__ = (
        Index("ix_chat_event_sent", "event_id", "sent_at"),
        Index("ix_chat_session_sent", "session_id", "sent_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id", ondelete="SET NULL"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime, default=utcnow, nullable=False, index=True)
    is_question = db.Column(db.Boolean, default=False, nullable=False)

    event = db.relationship("Event", back_populates="chat_messages")
    session = db.relationship("Session", back_populates="chat_messages")
    user = db.relationship("User", back_populates="chat_messages")

    def __repr__(self) -> str:
        return f"<ChatMessage event={self.event_id} user={self.user_id}>"


# ---------------------------------------------------------------------------
# Certificate
# ---------------------------------------------------------------------------


class Certificate(db.Model):
    """Certificate issued to a participant after event completion."""

    __tablename__ = "certificates"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_certificate_user_event"),
        Index("ix_certificates_event", "event_id"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    certificate_url = db.Column(db.String(512), nullable=False)
    issued_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="certificates")
    event = db.relationship("Event", back_populates="certificates")

    def __repr__(self) -> str:
        return f"<Certificate user={self.user_id} event={self.event_id}>"


# ---------------------------------------------------------------------------
# Notification
# ---------------------------------------------------------------------------


class Notification(db.Model):
    """In-app notification for a user."""

    __tablename__ = "notifications"
    __table_args__ = (Index("ix_notifications_user_read", "user_id", "is_read"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    user = db.relationship("User", back_populates="notifications")

    def __repr__(self) -> str:
        return f"<Notification user={self.user_id} title={self.title[:20]}>"


# ---------------------------------------------------------------------------
# SQLAlchemy event listeners
# ---------------------------------------------------------------------------


@event.listens_for(PollResponse, "after_insert")
def increment_poll_option_vote_count(_mapper, connection, target: PollResponse) -> None:
    """Denormalize vote_count on PollOption when a response is inserted."""
    connection.execute(
        update(PollOption.__table__)
        .where(PollOption.__table__.c.id == target.poll_option_id)
        .values(vote_count=PollOption.__table__.c.vote_count + 1)
    )


@event.listens_for(PollResponse, "after_delete")
def decrement_poll_option_vote_count(_mapper, connection, target: PollResponse) -> None:
    """Decrement vote_count when a response is removed."""
    connection.execute(
        update(PollOption.__table__)
        .where(PollOption.__table__.c.id == target.poll_option_id)
        .values(vote_count=PollOption.__table__.c.vote_count - 1)
    )


# ---------------------------------------------------------------------------
# Seed helpers
# ---------------------------------------------------------------------------

DEFAULT_ROLES = [
    {"name": "admin", "description": "System administrator with full access"},
    {"name": "organizer", "description": "Creates and manages virtual events"},
    {"name": "participant", "description": "Registers for and attends events"},
]


def seed_roles() -> None:
    """Insert default roles if they do not exist."""
    for role_data in DEFAULT_ROLES:
        if not Role.query.filter_by(name=role_data["name"]).first():
            db.session.add(Role(**role_data))
    db.session.commit()


def generate_confirmation_code() -> str:
    """Generate a unique registration confirmation code."""
    return secrets.token_hex(16)


__all__ = [
    "Role",
    "User",
    "Event",
    "EventStatus",
    "Session",
    "Registration",
    "RegistrationStatus",
    "Feedback",
    "Poll",
    "PollOption",
    "PollResponse",
    "ChatMessage",
    "Certificate",
    "Notification",
    "seed_roles",
    "generate_confirmation_code",
    "utcnow",
]
