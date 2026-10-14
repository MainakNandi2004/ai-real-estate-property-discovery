# Real Estate AI

AI-powered property discovery and lead generation. PostgreSQL is the source of truth for all factual property data.

## Prerequisites

- Python 3.11+
- PostgreSQL 14+

## Setup

```powershell
cd "c:\Users\MAINAK NANDI\OneDrive\Desktop\real estate ai"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env
```

Edit `.env` and set `DATABASE_URL`, for example:

`postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/real_estate_ai`

Create the database in PostgreSQL, then run migrations:

```powershell
alembic upgrade head
```

## Run API (health checks only for early phases)

```powershell
uvicorn app.main:app --reload
```

- `GET /health` — process liveness  
- `GET /health/db` — PostgreSQL connectivity  

## Tests

Uses `TEST_DATABASE_URL` if set, otherwise `DATABASE_URL`. The test suite runs Alembic migrations and uses transactional fixtures.

```powershell
pytest
```

## Architecture

- `app/models` — SQLAlchemy ORM  
- `app/repositories` — database access only  
- `app/services/search` — deterministic search, matching, ranking  
- `app/ai` — LLM integration (later phases)  
- `app/api` — FastAPI routes (Phase 13)  

Property data is maintained manually; this repository does not ship sample listings.

## Specification

See `real estate ai flowchart.md` for the master development flow.
