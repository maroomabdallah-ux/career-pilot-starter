# CareerPilot AI

CareerPilot is a multi-user career SaaS foundation built with FastAPI, PostgreSQL, and React. This phase includes authentication, onboarding, protected current-user profile CRUD, and responsive public/application layouts. AI, payments, OAuth, and job integrations are intentionally not enabled.

## Development URLs

- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

## Backend setup

```bash
cd career-pilot-backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
docker compose -f docker-compose.dev.yml up -d
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Set a unique `JWT_SECRET_KEY` of at least 32 random bytes in `.env`. Existing pre-auth development users are preserved by the migration with a nullable password hash, but cannot log in; recreate them through signup. No fake password is assigned.

Key variables: `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `FRONTEND_URL`, `CORS_ORIGINS`, and `ENVIRONMENT`.

## Frontend setup

```bash
cd career-pilot-frontend
npm install
npm run dev
```

Set `VITE_API_BASE_URL=http://localhost:8000/api/v1` when not using Vite's development proxy.

## Authentication flow

Signup/login returns a 15-minute access token held only in memory. A rotating refresh token is stored in an HttpOnly, SameSite=Lax cookie for 14 days. App bootstrap refreshes the session. Logout revokes the current database session and clears the cookie.

Authenticated profile routes live under `/api/v1/me`. Ownership comes from the validated JWT user, never a browser-supplied `user_id` or `profile_id`. Legacy UUID CRUD code remains for development compatibility but is not mounted by default; `ENABLE_LEGACY_CRUD_ROUTES=true` is an explicit unsafe development option and must not be used in shared environments.

## Verification

```bash
cd career-pilot-backend
.venv/bin/ruff check app tests
.venv/bin/pytest -q
ENVIRONMENT=test RUN_DATABASE_TESTS=1 .venv/bin/pytest -q

cd ../career-pilot-frontend
npm run build
```

Database integration tests require the migrated Docker PostgreSQL service. `.env`, `.venv`, `node_modules`, and build output are ignored by Git.
