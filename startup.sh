#!/bin/bash
# Azure App Service (Linux) startup script for Flask + gunicorn.
# Set this as the Startup Command in Azure Portal → App Service → Configuration → General settings:
#   startup.sh
#
# Or paste directly:
#   gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout 120 wsgi:app

set -e
exec gunicorn --bind=0.0.0.0:8000 --workers=2 --timeout 120 wsgi:app
