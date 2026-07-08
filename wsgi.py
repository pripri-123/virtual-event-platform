"""Production WSGI entry point for Azure App Service.

Azure App Service (Linux) startup command:
    gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout 120 wsgi:app
"""

from app import create_app

app = create_app(config_name="production")
