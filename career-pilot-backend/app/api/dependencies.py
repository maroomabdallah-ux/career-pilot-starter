from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.context import ai_user_id
from app.core.exceptions import AuthenticationError, ProfileAccessDeniedError
from app.core.security import decode_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

SessionDep = Annotated[AsyncSession, Depends(get_db)]
bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    session: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> User:
    if not credentials:
        raise AuthenticationError()
    try:
        payload = decode_token(credentials.credentials, "access")
        user = await UserRepository(session).get_by_id(UUID(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AuthenticationError("Invalid or expired access token") from None
    if not user or not user.is_active:
        raise AuthenticationError("Invalid or expired access token")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_ai_user(user: CurrentUser) -> AsyncIterator[User]:
    with ai_user_id(user.id):
        yield user


AIUser = Annotated[User, Depends(get_ai_user)]


async def get_admin_user(user: CurrentUser) -> User:
    if not user.is_admin:
        raise ProfileAccessDeniedError("Administrator access required")
    return user


AdminUser = Annotated[User, Depends(get_admin_user)]


async def get_current_access_token(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    """Forward the already-authenticated request credential to trusted internal clients."""
    if not credentials:
        raise AuthenticationError()
    try:
        decode_token(credentials.credentials, "access")
    except (jwt.PyJWTError, KeyError, ValueError):
        raise AuthenticationError("Invalid or expired access token") from None
    return credentials.credentials


AccessTokenDep = Annotated[str, Depends(get_current_access_token)]
