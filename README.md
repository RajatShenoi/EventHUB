# Event Management Platform (Flask + React + SQLite)

Event management web app with role-based workflows for admins and users.

## Implemented Features

### User features
- Register and login.
- Browse events and open event detail pages.
- Register for open/ongoing events using event-specific dynamic fields.
- Receive a check-in QR after successful registration.
- If already registered for an event, see existing QR instead of re-registering.
- Cancel registration only when not checked in.
- View own registrations.
- View event results after completion.

### Admin features
- Login and manage events.
- Full event CRUD and status transitions (`open`, `ongoing`, `completed`, delete).
- Build event registration forms dynamically (text/email/phone/textarea/select/radio).
- Add and remove custom fields while creating events.
- Scan check-in QR directly inside individual event pages.
- Event-scoped check-in validation (QR from a different event is rejected).
- Publish event results from individual event pages.
- Result publish table includes participant ID, name, and submitted registration fields.
- Enter marks; rank is auto-calculated.
- Publish results only for checked-in users.
- Manage users from admin users page (view, edit role, delete).

### Role and access policy
- Admins cannot register for events.
- Users cannot request admin role.
- Role updates are performed by existing admins from the users page.

## Project Structure

- `backend/` Flask API
- `frontend/` React (Vite)

## Backend Setup

1. `cd backend`
2. `python3 -m venv .venv`
3. `source .venv/bin/activate`
4. `pip install -r requirements.txt`
5. `cp .env.example .env`
6. `python run.py`

API runs at `http://localhost:5000`.

### Bootstrap first admin

Use this once:

```bash
curl -X POST http://localhost:5000/api/admin/bootstrap \
  -H "Content-Type: application/json" \
  -d '{"setup_token":"LOCAL_SETUP_TOKEN","email":"admin@local.dev","password":"Admin@1234","full_name":"Admin"}'
```

## Frontend Setup

1. `cd frontend`
2. `npm install`
3. `cp .env.example .env`
4. `npm run dev`

Frontend runs at `http://localhost:5173`.

## API Summary

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Events
- `GET /api/events`
- `GET /api/events/:id`
- `POST /api/events` (admin)
- `PUT /api/events/:id` (admin)
- `DELETE /api/events/:id` (admin)

### Registrations (user only)
- `POST /api/registrations`
- `GET /api/registrations`
- `PUT /api/registrations/:id`
- `DELETE /api/registrations/:id`

### Check-in (admin)
- `POST /api/checkin/scan` (supports `event_id` for event-scoped validation)
- `GET /api/checkin/history`
- `GET /api/checkin/history?event_id={event_id}`

### Results
- `GET /api/results/event/:event_id` (user/admin, role-filtered output)
- `GET /api/results/event/:event_id/participants` (admin)
- `POST /api/results/event/:event_id/publish` (admin, auto-rank)
- `POST /api/results/event/:event_id` (admin, single-entry helper)

### Admin users
- `GET /api/admin/users`
- `PUT /api/admin/users/:id`
- `DELETE /api/admin/users/:id`

## Notes

- SQLite is used via SQLAlchemy.
- SQLite foreign keys are enabled on connection.
- QR tokens are signed server-side and rendered as PNG data URLs.
- Duplicate scans return `already_checked_in` and do not mutate state.
- User result view hides global attendance and other users' remarks.

## Suggested Next Improvements

- Add Alembic migrations (instead of `create_all` bootstrap).
- Add backend/frontend test suites.
- Add CSV import/export for results.
- Add production deployment setup (WSGI/reverse proxy).
