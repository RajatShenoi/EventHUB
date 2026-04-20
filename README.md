# Event Management Platform (Flask + React + SQLite)

Production-style modular starter implementation with:
- Role-based login (`user`, `admin`)
- Event listing and event detail page
- Event-specific dynamic registration fields
- QR generation on successful registration
- Admin event CRUD
- Admin QR check-in with duplicate scan handling
- Post-event results (attendance + ranking)
- User registered-events page
- Admin role-request review flow

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

## Core API Endpoints

- Auth: `/api/auth/register`, `/api/auth/login`, `/api/auth/me`
- Events: `GET/POST /api/events`, `GET/PUT/DELETE /api/events/:id`
- Registrations: `POST/GET /api/registrations`, `PUT/DELETE /api/registrations/:id`
- Check-in: `POST /api/checkin/scan`, `GET /api/checkin/history`
- Results: `GET/POST /api/results/event/:event_id`
- Admin users: `GET /api/admin/users`, `PUT /api/admin/users/:id`, `DELETE /api/admin/users/:id`

## Notes

- SQLite is used through SQLAlchemy.
- QR token is signed server-side using `itsdangerous` and encoded as PNG for display.
- Duplicate check-in scans return `already_checked_in` without mutating state.
- Results are shown to users only after event status is `completed`.

## Next Enhancements

- Alembic migrations and seed scripts
- Refresh tokens and logout token revocation
- CSV import/export for rankings
- Full test suite (pytest + React Testing Library)
- Production WSGI serving and reverse proxy config
