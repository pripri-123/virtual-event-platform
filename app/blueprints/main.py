"""Main blueprint — public pages and health check."""

from flask import Blueprint, render_template, jsonify

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Home page — landing page for the platform."""
    return render_template("main/index.html")


@main_bp.route("/health")
def health():
    """Health check endpoint for Azure App Service and load balancers."""
    return jsonify({"status": "healthy", "service": "virtual-event-platform"}), 200
