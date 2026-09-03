import logging

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ProfileAccessDeniedError,
)

logger = logging.getLogger(__name__)


async def request_validation_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    if settings.ENVIRONMENT == "development":
        # Do not log input values: validation payloads may contain private profile data.
        errors = [
            {
                "location": [str(part) for part in error["loc"]],
                "type": error["type"],
                "message": error["msg"],
            }
            for error in exc.errors()
        ]
        logger.warning(
            "API request validation failed",
            extra={
                "validation": {
                    "method": request.method,
                    "path": request.url.path,
                    "errors": errors,
                }
            },
        )
    return JSONResponse(
        status_code=422,
        content=jsonable_encoder({"detail": exc.errors()}),
    )


async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.detail})


async def conflict_handler(_: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": exc.detail})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(RequestValidationError, request_validation_handler)
    app.add_exception_handler(NotFoundError, not_found_handler)
    app.add_exception_handler(ConflictError, conflict_handler)
    app.add_exception_handler(
        AuthenticationError,
        lambda _, exc: JSONResponse(
            status_code=401, content={"detail": exc.detail}, headers={"WWW-Authenticate": "Bearer"}
        ),
    )
    app.add_exception_handler(
        ProfileAccessDeniedError,
        lambda _, exc: JSONResponse(status_code=403, content={"detail": exc.detail}),
    )
