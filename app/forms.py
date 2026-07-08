"""WTForms form definitions with CSRF protection."""

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, ValidationError

from app.models import EventStatus, User


EVENT_CATEGORIES = [
    ("", "Select category"),
    ("conference", "Conference"),
    ("workshop", "Workshop"),
    ("webinar", "Webinar"),
    ("meetup", "Meetup"),
    ("other", "Other"),
]


class LoginForm(FlaskForm):
    """User login form."""

    email = StringField(
        "Email",
        validators=[DataRequired(message="Email is required."), Email(message="Invalid email address.")],
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(message="Password is required.")],
    )
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Log In")


class RegisterForm(FlaskForm):
    """New user registration form."""

    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(message="Full name is required."),
            Length(min=2, max=120, message="Name must be between 2 and 120 characters."),
        ],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(message="Email is required."), Email(message="Invalid email address.")],
    )
    role = SelectField(
        "Register As",
        choices=[
            ("participant", "Participant — attend events"),
            ("organizer", "Organizer — create and manage events"),
        ],
        validators=[DataRequired()],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required."),
            Length(min=8, message="Password must be at least 8 characters."),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Please confirm your password."),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field) -> None:
        """Ensure email is not already registered."""
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("An account with this email already exists.")


class EventForm(FlaskForm):
    """Create or edit an event."""

    title = StringField(
        "Event Title",
        validators=[
            DataRequired(message="Title is required."),
            Length(min=3, max=200, message="Title must be 3–200 characters."),
        ],
    )
    description = TextAreaField(
        "Description",
        validators=[Length(max=5000, message="Description is too long.")],
        render_kw={"rows": 5},
    )
    category = SelectField("Category", choices=EVENT_CATEGORIES, validators=[DataRequired()])
    start_datetime = StringField(
        "Start Date & Time",
        validators=[DataRequired(message="Start date is required.")],
        render_kw={"type": "datetime-local"},
    )
    end_datetime = StringField(
        "End Date & Time",
        validators=[DataRequired(message="End date is required.")],
        render_kw={"type": "datetime-local"},
    )
    max_capacity = IntegerField(
        "Maximum Attendees",
        validators=[
            DataRequired(message="Capacity is required."),
            NumberRange(min=1, max=10000, message="Capacity must be between 1 and 10,000."),
        ],
        default=100,
    )
    status = SelectField(
        "Status",
        choices=[
            (EventStatus.DRAFT.value, "Draft — not visible to attendees"),
            (EventStatus.PUBLISHED.value, "Published — open for registration"),
            (EventStatus.CANCELLED.value, "Cancelled"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Save Event")


class QuestionForm(FlaskForm):
    """Submit a Q&A question for an event."""

    message = TextAreaField(
        "Your Question",
        validators=[
            DataRequired(message="Please enter your question."),
            Length(min=5, max=1000, message="Question must be 5–1000 characters."),
        ],
        render_kw={"rows": 3, "placeholder": "Ask the organizer or speaker a question..."},
    )
    submit = SubmitField("Post Question")


__all__ = [
    "FlaskForm",
    "LoginForm",
    "RegisterForm",
    "EventForm",
    "QuestionForm",
    "EVENT_CATEGORIES",
]
