"""
POST /api/ai/search

Thin FastAPI route. All orchestration is in AISearchService.
"""
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ai_search import (
    AISearchErrorResponse,
    AISearchRequest,
    AISearchResponse,
)
from app.services.ai_search_service import AISearchError, AISearchErrorKind, AISearchService

router = APIRouter(prefix="/api/ai", tags=["AI Search"])

# Map AISearchErrorKind → HTTP status code
_ERROR_STATUS_MAP = {
    AISearchErrorKind.INSUFFICIENT_REQUIREMENTS: status.HTTP_422_UNPROCESSABLE_ENTITY,
    AISearchErrorKind.EXTRACTION_FAILED: status.HTTP_502_BAD_GATEWAY,
    AISearchErrorKind.SEARCH_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
}


@router.post(
    "/search",
    response_model=AISearchResponse,
    responses={
        200: {"description": "Search completed (exact, partial, or no matches)."},
        422: {"model": AISearchErrorResponse, "description": "Query too vague — clarification needed."},
        502: {"model": AISearchErrorResponse, "description": "AI extraction failed (Gemini unavailable)."},
        500: {"model": AISearchErrorResponse, "description": "Database or search error."},
    },
    summary="Natural-language property search",
    description=(
        "Submit a plain-English property query. "
        "Gemini extracts structured requirements; PostgreSQL finds matching properties. "
        "Gemini never accesses the database directly."
    ),
)
def ai_search(
    request: AISearchRequest,
    db: Session = Depends(get_db),
) -> JSONResponse:
    service = AISearchService(db)
    result = service.search_from_query(request.query)

    if isinstance(result, AISearchError):
        http_status = _ERROR_STATUS_MAP.get(result.kind, status.HTTP_500_INTERNAL_SERVER_ERROR)
        body = AISearchErrorResponse(
            status=result.kind.value,
            query=request.query,
            message=result.message,
        )
        return JSONResponse(status_code=http_status, content=body.model_dump())

    body = AISearchResponse.from_outcome(request.query, result)
    return JSONResponse(status_code=status.HTTP_200_OK, content=body.model_dump(mode="json"))
