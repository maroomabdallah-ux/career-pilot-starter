from __future__ import annotations

import logging
import time
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any, TypeVar
from uuid import UUID

from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.fastmcp.exceptions import ToolError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.repositories.user import UserRepository

logger = logging.getLogger(__name__)
ResultT = TypeVar("ResultT")


@asynccontextmanager
async def authenticated_context() -> AsyncIterator[tuple[AsyncSession, User]]:
    """Resolve the trusted MCP bearer subject and its active CareerPilot user."""
    access = get_access_token()
    if not access or not access.subject:
        raise ToolError("Authentication required")
    try:
        user_id = UUID(access.subject)
    except ValueError as exc:
        raise ToolError("Invalid authenticated subject") from exc

    async with AsyncSessionLocal() as session:
        user = await UserRepository(session).get_by_id(user_id)
        if not user or not user.is_active:
            raise ToolError("Authenticated user is unavailable")
        yield session, user


async def run_tool(
    name: str,
    operation: Callable[[AsyncSession, User], Awaitable[ResultT]],
) -> ResultT:
    started = time.perf_counter()
    user_id = "unresolved"
    try:
        async with authenticated_context() as (session, user):
            user_id = str(user.id)
            result = await operation(session, user)
        logger.info(
            "MCP tool completed",
            extra={
                "mcp": {
                    "tool": name,
                    "success": True,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 2),
                    "user_id": user_id,
                }
            },
        )
        return result
    except ToolError:
        _log_failure(name, started, user_id)
        raise
    except ValueError as exc:
        _log_failure(name, started, user_id)
        raise ToolError(str(exc)) from exc
    except Exception as exc:
        _log_failure(name, started, user_id, exception=True)
        raise ToolError("CareerPilot could not complete this read operation") from exc


def _log_failure(name: str, started: float, user_id: str, *, exception: bool = False) -> None:
    details: dict[str, Any] = {
        "tool": name,
        "success": False,
        "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        "user_id": user_id,
    }
    if exception:
        logger.exception("MCP tool failed", extra={"mcp": details})
    else:
        logger.warning("MCP tool failed", extra={"mcp": details})
