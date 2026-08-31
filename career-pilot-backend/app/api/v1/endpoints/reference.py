from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services.reference_data import UniversityProviderError, UniversityReferenceService

router = APIRouter()


@router.get("/universities")
async def universities(
    q: str = Query(min_length=2, max_length=100),
    country: str | None = Query(default=None, max_length=100),
    limit: int = Query(default=25, ge=1, le=30),
):
    try:
        return await UniversityReferenceService().search(q.strip(), country, limit)
    except UniversityProviderError:
        return JSONResponse(
            status_code=503,
            content={
                "detail": (
                    "University search is temporarily unavailable. "
                    "Manual entry is still available."
                )
            },
        )
