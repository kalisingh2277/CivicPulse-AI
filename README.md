# CivicPulse AI — Predictive Urban Governance Platform

Citizen complaints in (any language) → AI dedupes them into **issues** → prioritized department work queues → city-wide analytics, hotspots, and forecasts. Pilot city: Bengaluru.

**Planning docs (read first):** [docs/README.md](docs/README.md) — PRD, user flows, DB schema, API contracts, architecture (+ADRs), build plan.

## Stack

Next.js 16 + Tailwind · FastAPI · PostgreSQL 16 (PostGIS + pgvector) · Redis + arq · MinIO/R2 · multilingual-e5 embeddings · Gemini Flash (adapter + mock mode) · Docker

## Quickstart (dev)

Prereqs: Docker Desktop, Node 22 + pnpm, uv.

```powershell
# 1. infra (postgres+postgis+pgvector, redis, minio)
docker compose up -d

# 2. backend env + migrations + seed + API
Copy-Item .env.example backend\.env
cd backend
uv run alembic upgrade head
uv run python -m scripts.seed          # departments, categories, 243 BBMP wards
uv run uvicorn app.main:app --reload --port 8000

# 3. frontend (new terminal)
cd frontend
pnpm dev
```

Open http://localhost:3000 — the Day-1 page shows live health of every infra piece.
API docs (auto-generated OpenAPI): http://localhost:8000/api/v1/docs
MinIO console: http://localhost:9001 (civicpulse / civicpulse123)

## Tests & lint

```powershell
cd backend
uv run pytest -m "not integration"   # unit (CI runs these)
uv run pytest                        # + integration (needs docker compose up)
uv run ruff check . ; uv run ruff format --check .
```

## Repository layout

```
docs/        planning documents — PRD, schema, API contracts, architecture ADRs, build plan
backend/     FastAPI app, arq workers, Alembic migrations, tests
frontend/    Next.js app (citizen portal, official console, admin, public dashboard)
infra/       custom Postgres image (PostGIS + pgvector)
ml/          eval sets + notebooks (from Day 5)
```
