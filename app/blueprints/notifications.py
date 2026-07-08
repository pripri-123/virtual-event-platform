"""In-app notifications for users."""

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Notification

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@notifications_bp.route("/")
@login_required
def list_notifications():
    """View all notifications for the current user."""
    notifications = (
        Notification.query.filter_by(user_id=current_user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )
    return render_template("notifications/list.html", notifications=notifications)


@notifications_bp.route("/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_read(notification_id: int):
    """Mark a single notification as read."""
    notification = db.session.get(Notification, notification_id)
    if notification and notification.user_id == current_user.id:
        notification.is_read = True
        db.session.commit()
    return redirect(url_for("notifications.list_notifications"))


@notifications_bp.route("/read-all", methods=["POST"])
@login_required
def mark_all_read():
    """Mark all notifications as read."""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update(
        {"is_read": True}
    )
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for("notifications.list_notifications"))
