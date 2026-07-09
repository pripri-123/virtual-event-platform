"""MVP smoke test — events, registration, Q&A, notifications."""

import re
import sys
import uuid

from app import create_app
from app.models import Event, Notification, Registration


def get_csrf(html: str) -> str:
    match = re.search(r'csrf_token.*?value="([^"]+)"', html, re.DOTALL)
    if not match:
        raise ValueError("CSRF token not found")
    return match.group(1)


def main() -> int:
    app = create_app("development")
    client = app.test_client()

    # Organizer login
    r = client.get("/auth/login")
    csrf = get_csrf(r.data.decode())
    r = client.post(
        "/auth/login",
        data={"email": "organizer@vehp.com", "password": "Organizer@123", "csrf_token": csrf},
        follow_redirects=True,
    )
    assert r.status_code == 200 and "/dashboard/organizer" in r.request.path
    print("Organizer login: OK")

    # Create event
    r = client.get("/events/create")
    csrf = get_csrf(r.data.decode())
    from datetime import datetime, timedelta

    start = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M")
    end = (datetime.now() + timedelta(days=7, hours=2)).strftime("%Y-%m-%dT%H:%M")
    title = f"Test Event {uuid.uuid4().hex[:6]}"
    r = client.post(
        "/events/create",
        data={
            "title": title,
            "description": "MVP test event",
            "category": "webinar",
            "start_datetime": start,
            "end_datetime": end,
            "max_capacity": 10,
            "status": "published",
            "csrf_token": csrf,
        },
        follow_redirects=True,
    )
    assert r.status_code == 200
    print("Create event: OK")

    with app.app_context():
        event = Event.query.filter_by(title=title).first()
        assert event is not None
        event_id = event.id

    # Logout
    r = client.get("/dashboard/organizer")
    csrf = get_csrf(r.data.decode())
    client.post("/auth/logout", data={"csrf_token": csrf}, follow_redirects=True)

    # Participant login and register
    r = client.get("/auth/login")
    csrf = get_csrf(r.data.decode())
    r = client.post(
        "/auth/login",
        data={"email": "participant@vehp.com", "password": "Participant@123", "csrf_token": csrf},
        follow_redirects=True,
    )
    assert "/dashboard/participant" in r.request.path
    print("Participant login: OK")

    r = client.get(f"/events/{event_id}")
    csrf = get_csrf(r.data.decode())
    r = client.post(f"/registrations/{event_id}/register", data={"csrf_token": csrf}, follow_redirects=True)
    assert r.status_code == 200
    print("Registration: OK")

    with app.app_context():
        reg = Registration.query.filter_by(event_id=event_id).first()
        assert reg is not None
        notifs = Notification.query.count()
        assert notifs >= 2  # attendee + organizer notifications
    print("Notifications: OK")

    # Q&A
    r = client.get(f"/events/{event_id}/qa")
    csrf = get_csrf(r.data.decode())
    r = client.post(
        f"/events/{event_id}/qa",
        data={"message": "What topics will be covered?", "csrf_token": csrf},
        follow_redirects=True,
    )
    assert b"What topics will be covered?" in r.data
    print("Q&A: OK")

    print("All MVP tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
