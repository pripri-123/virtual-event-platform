"""Azure Application Insights telemetry initialization."""

from __future__ import annotations

from flask import Flask


def init_telemetry(app: Flask) -> None:
    """Configure OpenTelemetry + Application Insights when connection string is set."""
    conn_str = app.config.get("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    if not conn_str:
        app.logger.info("Application Insights not configured — skipping telemetry.")
        return

    try:
        from azure.monitor.opentelemetry import configure_azure_monitor
        from opentelemetry.instrumentation.flask import FlaskInstrumentor

        configure_azure_monitor(connection_string=conn_str)
        FlaskInstrumentor().instrument_app(app)
        app.logger.info("Application Insights telemetry enabled.")
    except Exception as exc:  # noqa: BLE001 — telemetry must never block startup
        app.logger.warning("Failed to initialize Application Insights: %s", exc)
