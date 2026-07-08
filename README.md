# Virtual Event Hosting Platform

A user-friendly virtual event platform built with **Flask** and **Microsoft Azure SQL Database**.

## MVP Features (Current)

| Feature | Who | Description |
|---------|-----|-------------|
| **Event management** | Organizers | Create, edit, delete, publish events |
| **Browse & search** | Everyone | Find published events with search/filter |
| **Registration** | Participants | Register, cancel, view confirmation code |
| **Q&A** | Registered users | Ask questions per event (no live video/links) |
| **Notifications** | All users | In-app alerts for registrations |
| **Dashboards** | All roles | Live stats from the database |

**Deferred for later iterations:** live sessions, meeting links, Azure Blob, Functions, certificates, polls.

## Analytics

Role dashboards include live **Chart.js** visualizations powered by database queries:

| Dashboard | Charts |
|-----------|--------|
| **Admin** | Registration trend (30 days), events by status, users by role, events by category |
| **Organizer** | Registration trend, registrations per event, events by status/category |
| **Participant** | Registered event categories |

**Application Insights** telemetry is enabled automatically when `APPLICATIONINSIGHTS_CONNECTION_STRING` is set in `.env`.

## Quick Start

```powershell
cd C:\Users\xoxan\Projects\virtual-event-platform
.\venv\Scripts\Activate.ps1
Copy-Item .env.example .env   # first time only

flask db upgrade
flask seed-demo
python run.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000)

### Demo Accounts

| Role | Email | Password |
|------|-------|----------|
| Organizer | organizer@vehp.com | Organizer@123 |
| Participant | participant@vehp.com | Participant@123 |
| Admin | admin@vehp.com | Admin@123 |

## Azure SQL Database

Local development uses **SQLite** (`instance/vehp.db`). For production / college deployment, configure **Azure SQL**:

1. Install ODBC Driver 18 and `pip install -r requirements-azure.txt`
2. Create Azure SQL Server + Database in Azure Portal
3. Set firewall rule for your IP
4. Add to `.env`:

```env
AZURE_SQL_SERVER=your-server-name
AZURE_SQL_DATABASE=vehp-db
AZURE_SQL_USERNAME=vehpadmin
AZURE_SQL_PASSWORD=your-strong-password
FLASK_ENV=production
```

5. Deploy schema and seed data:

```powershell
.\scripts\deploy-azure-sql.ps1
```

Or manually:

```powershell
flask db-check-azure   # test connection
flask db upgrade
flask seed-roles
flask seed-demo
```

## Run Tests

```powershell
$env:PYTHONPATH = "C:\Users\xoxan\Projects\virtual-event-platform"
python tests\test_auth_smoke.py
python tests\test_mvp_smoke.py
```

## Modified Roadmap

| Phase | Status | Scope |
|-------|--------|-------|
| 1–5 | Done | Planning, setup, structure, DB, auth |
| **MVP** | **Done** | Events, registration, Q&A, notifications, dashboards |
| **Azure SQL + Analytics** | **Done** | Azure SQL deploy script, dashboard charts, Application Insights |
| Next | Planned | Azure App Service deploy, recommendations |

## Project Structure

```
app/
├── blueprints/
│   ├── auth.py           # Login / register
│   ├── dashboard.py      # Role dashboards with stats
│   ├── events.py         # Event CRUD + browse
│   ├── registrations.py  # Attendee registration
│   ├── qa.py             # Event Q&A
│   └── notifications.py  # In-app notifications
├── services/
│   └── notification_service.py
├── models.py             # 12-table schema
├── forms.py
└── templates/
```

## License

Educational / college final-year project.
