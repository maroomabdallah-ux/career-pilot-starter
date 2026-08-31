from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    ProfileAccessDeniedError,
)


async def not_found_handler(_: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.detail})


async def conflict_handler(_: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": exc.detail})


def register_exception_handlers(app: FastAPI) -> None:
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
