from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.ai_search import router as ai_search_router
from app.config import get_settings
from app.db.session import check_database_connection

settings = get_settings()

app = FastAPI(
    title="Real Estate AI API",
    version="0.1.0",
    description=(
        "AI-powered real estate property search. "
        "Natural-language queries are parsed by Gemini into structured criteria; "
        "PostgreSQL is the single source of truth for all property data."
    ),
    debug=settings.debug,
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(ai_search_router)


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Status"], summary="API root")
def root() -> dict:
    return {
        "name": "Real Estate AI API",
        "version": "0.1.0",
        "status": "ok",
        "docs": "/docs",
    }


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["Status"], summary="Liveness probe")
def health_liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["Status"], summary="Database connectivity check")
def health_database() -> dict[str, str | bool]:
    ok, detail = check_database_connection()
    return {
        "status": "ok" if ok else "error",
        "database": detail,
        "connected": ok,
    }
