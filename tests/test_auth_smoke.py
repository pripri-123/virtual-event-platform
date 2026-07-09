"""Quick Phase 5 authentication smoke test — run: python tests/test_auth_smoke.py"""

import re
import sys
import uuid

from app import create_app
from app.models import User


def get_csrf(html: str) -> str:
    match = re.search(r'csrf_token.*?value="([^"]+)"', html, re.DOTALL)
    if not match:
        raise ValueError("CSRF token not found")
    return match.group(1)


def main() -> int:
    app = create_app("development")
    client = app.test_client()
    test_email = f"participant_{uuid.uuid4().hex[:8]}@test.com"

    # Register participant
    response = client.get("/auth/register")
    csrf = get_csrf(response.data.decode())
    response = client.post(
        "/auth/register",
        data={
            "full_name": "Jane Participant",
            "email": test_email,
            "role": "participant",
            "password": "SecurePass1",
            "confirm_password": "SecurePass1",
            "csrf_token": csrf,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "/auth/login" in response.request.path
    print("Register: OK")

    # Login participant
    response = client.get("/auth/login")
    csrf = get_csrf(response.data.decode())
    response = client.post(
        "/auth/login",
        data={
            "email": test_email,
            "password": "SecurePass1",
            "remember_me": True,
            "csrf_token": csrf,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "/dashboard/participant" in response.request.path
    print("Login participant: OK")

    # Role protection
    response = client.get("/dashboard/organizer")
    assert response.status_code == 403
    print("Role protection: OK")

    # Logout — get CSRF from authenticated page (navbar logout form)
    response = client.get("/dashboard/participant")
    csrf = get_csrf(response.data.decode())
    response = client.post("/auth/logout", data={"csrf_token": csrf}, follow_redirects=True)
    assert response.status_code == 200
    print("Logout: OK")

    # Admin login
    response = client.get("/auth/login")
    csrf = get_csrf(response.data.decode())
    response = client.post(
        "/auth/login",
        data={
            "email": "admin@vehp.com",
            "password": "Admin@123",
            "csrf_token": csrf,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "/dashboard/admin" in response.request.path
    print("Admin login: OK")

    with app.app_context():
        user = User.query.filter_by(email=test_email).first()
        assert user is not None
        assert user.password_hash != "SecurePass1"
    print("Password hashing: OK")

    print("All Phase 5 tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
