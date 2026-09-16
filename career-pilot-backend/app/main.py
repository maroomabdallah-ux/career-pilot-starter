import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exception_handlers import register_exception_handlers
from app.db.session import AsyncSessionLocal
from app.middleware.ai_correlation import AIRequestCorrelationMiddleware
from app.middleware.security import SecurityMiddleware
from app.api.v1.endpoints.jobs import direct_job_search
from app.schemas.job import JobSearchCriteria

logger = logging.getLogger(__name__)


async def warm_jobs():
    while True:
        try:
            await direct_job_search.search(JobSearchCriteria(query="", limit=50))
        except Exception as exc:
            logger.warning("Job catalog refresh failed: error_type=%s error=%s", type(exc).__name__, exc)
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    task = asyncio.create_task(warm_jobs())
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)
app.add_middleware(SecurityMiddleware)
app.add_middleware(AIRequestCorrelationMiddleware)
register_exception_handlers(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": settings.APP_NAME}


@app.get("/ready", tags=["health"])
async def readiness_check():
    async with AsyncSessionLocal() as session:
        await session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
