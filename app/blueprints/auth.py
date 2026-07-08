"""Authentication blueprint — register, login, logout."""

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user

from app.extensions import db
from app.forms import LoginForm, RegisterForm
from app.models import Role, User, utcnow
from app.utils import get_dashboard_url_for_role, hash_password, verify_password

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Create a new participant or organizer account."""
    if current_user.is_authenticated:
        return redirect(get_dashboard_url_for_role(current_user.role_name))

    form = RegisterForm()
    if form.validate_on_submit():
        role = Role.query.filter_by(name=form.role.data).first()
        if role is None:
            flash("Invalid role selected.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            role_id=role.id,
            email=form.email.data.lower().strip(),
            password_hash=hash_password(form.password.data),
            full_name=form.full_name.data.strip(),
            is_active=True,
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate user and start a session."""
    if current_user.is_authenticated:
        return redirect(get_dashboard_url_for_role(current_user.role_name))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.lower().strip()
        user = User.query.filter_by(email=email).first()

        if user is None or not verify_password(user.password_hash, form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth/login.html", form=form)

        if not user.is_active:
            flash("Your account has been deactivated. Contact an administrator.", "warning")
            return render_template("auth/login.html", form=form)

        user.last_login = utcnow()
        db.session.commit()

        login_user(user, remember=form.remember_me.data)
        flash(f"Welcome back, {user.full_name}!", "success")

        next_page = redirect(get_dashboard_url_for_role(user.role_name))
        return next_page

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """End the user session."""
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "info")
    return redirect(url_for("main.index"))
