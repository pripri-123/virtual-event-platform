"""Local development entry point.

Run with:
    python run.py

Or with Flask CLI:
    flask --app run.py run --debug
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config["DEBUG"])
