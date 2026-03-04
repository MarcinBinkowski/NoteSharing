# Notes

A secure, ephemeral note-sharing application. Create notes with optional password protection, expiration times, and burn-after-reading behaviour.

**Live:** [https://acc.mbinkowski.tech](https://acc.mbinkowski.tech)

---

## Features

- **Anonymous or authenticated** note creation — Google OAuth for account-linked notes
- **Password protection** — Argon2id hashing (OWASP-recommended parameters)
- **Expiration** — time-based TTL from 1 minute to 30 days
- **Burn after reading** — atomic single-read deletion (TOCTOU-safe)
- **JWT cookies** — httpOnly access (15 min) + refresh (7 days) cookie pair with silent rotation
- **Rate limiting** — slowapi with per-IP limits on sensitive endpoints
- **Security headers** — CSP, HSTS, X-Frame-Options, and more

---

## Architecture

```
notes/
├── backend/     # Python 3.14 · FastAPI · Pydantic v2 · Argon2id · JWT
├── frontend/    # React 19 · TypeScript · Vite · TanStack Router · shadcn/ui
└── infra/       # Terraform · GCP Cloud Run · Artifact Registry
```

### Backend layers

| Layer | Path | Purpose |
|-------|------|---------|
| Schemas | `app/schemas/` | Domain models + request/response DTOs |
| Repositories | `app/repositories/` | Storage abstraction (Protocol) |
| Services | `app/services/` | Business logic (plain async functions) |
| API | `app/api/` | FastAPI routes + DI + middleware |

Two storage backends share a common `NoteRepository` / `UserRepository` protocol:
- **Firestore** — production default (GCP free tier)
- **SQLite** — local development and testing (set `NOTES_DATABASE_BACKEND=sqlite`)

---

## Local development

### Prerequisites

- Python 3.14+ and [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- Docker (optional, for `docker compose up`)

### Backend

```bash
cd backend
uv sync --extra dev
source .venv/bin/activate
cp .env.example .env          # edit and fill in secrets
uvicorn app.main:app --reload  # http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env           # optional — only needed outside Docker
npm run dev                    # http://localhost:5173  (proxies /api → :8000)
```

### Docker Compose (recommended for full-stack local development)

```bash
cp backend/.env.example backend/.env  # edit with your secrets
docker compose up
# Backend:  http://localhost:8000
# Frontend: http://localhost:5173
```

---

## Common tasks

```bash
# Run tests (backend)
make test

# Lint (backend + frontend)
make lint

# Auto-format
make fmt

# Type-check
make typecheck

# Regenerate frontend API client (after any route change)
make regen-client

# Deploy to acceptance
make deploy ENV=acc

# Deploy to production
make deploy ENV=prod
```

---

## Environment variables

All backend variables are prefixed with `NOTES_`. See [`backend/.env.example`](backend/.env.example) for the full reference.

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTES_DATABASE_BACKEND` | `firestore` | `firestore` or `sqlite` |
| `NOTES_SECRET_KEY` | *(required in prod)* | JWT signing secret |
| `NOTES_SESSION_SECRET_KEY` | *(required in prod)* | OAuth session cookie secret |
| `NOTES_GOOGLE_CLIENT_ID` | — | Google OAuth client ID |
| `NOTES_GOOGLE_CLIENT_SECRET` | — | Google OAuth client secret |
| `NOTES_BACKEND_URL` | `http://localhost:8000` | Public backend URL (for OAuth redirect) |
| `NOTES_FRONTEND_URL` | `http://localhost:5173` | Public frontend URL (for CORS + redirects) |
| `NOTES_DEBUG` | `false` | Enables Swagger UI and relaxes some prod checks |
| `NOTES_RATE_LIMIT_DEFAULT` | `60/minute` | Default rate limit per IP |
| `NOTES_LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

---

## Testing

```bash
cd backend
pytest tests/ -v              # runs all tests with coverage report
pytest tests/ -v -k "Expired" # run a subset
```

Tests use a `_FakeFirestoreClient` in-memory backend — no real GCP credentials needed.

Coverage report is generated at `htmlcov/index.html`.

---

## Security notes

- Passwords are hashed with **Argon2id** (time=2, memory=19 MB, parallelism=1 — OWASP 2023 minimum)
- Password verification uses **constant-time** comparison to prevent timing oracles
- Auth cookies are **httpOnly** and **SameSite=Lax**; the refresh token is scoped to `/api/auth`
- All 401 responses from `/api/auth/me` clear stale cookies automatically
- Note deletion by non-owners returns **404** (not 403) to prevent ID enumeration
- CSP, HSTS, X-Frame-Options, Referrer-Policy headers on every response

---

## Deployment

Infrastructure is managed with Terraform (see [`infra/`](infra/)).

```bash
# One-time: create GCP infra
make infra ENV=acc

# Build, push image and deploy in one step
make deploy ENV=acc
```

See [`infra/modules/environment/variables.tf`](infra/modules/environment/variables.tf) for Terraform variables.

---

## License

MIT
