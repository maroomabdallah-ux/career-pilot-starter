from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsError,
    SessionExpiredError,
    SessionRevokedError,
    UserAlreadyExistsError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.auth_session import AuthSessionRepository
from app.repositories.user import UserRepository
from app.schemas.auth import SignupRequest


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.sessions = AuthSessionRepository(session)

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    async def signup(self, data: SignupRequest, user_agent: str | None):
        email = self.normalize_email(str(data.email))
        if await self.users.get_by_email(email):
            raise UserAlreadyExistsError()
        user = User(
            email=email,
            first_name=data.first_name.strip(),
            last_name=data.last_name.strip(),
            password_hash=hash_password(data.password),
        )
        self.session.add(user)
        try:
            await self.session.flush()
            result = await self.issue_session(user, user_agent)
            await self.session.commit()
            return result
        except IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsError() from None

    async def login(self, email: str, password: str, user_agent: str | None):
        user = await self.users.get_by_email(self.normalize_email(email))
        if (
            not user
            or not user.password_hash
            or not verify_password(password, user.password_hash)
            or not user.is_active
        ):
            raise InvalidCredentialsError()
        result = await self.issue_session(user, user_agent)
        await self.session.commit()
        return result

    async def issue_session(self, user: User, user_agent: str | None):
        jti = uuid4().hex
        expires_at = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.sessions.create(
            user_id=user.id,
            refresh_token_jti=jti,
            expires_at=expires_at,
            user_agent=(user_agent or "")[:512] or None,
        )
        return user, create_access_token(user.id), create_refresh_token(user.id, jti)

    async def refresh(self, token: str, user_agent: str | None):
        try:
            payload = decode_token(token, "refresh")
            user_id, jti = UUID(payload["sub"]), payload["jti"]
        except (jwt.PyJWTError, KeyError, ValueError):
            raise SessionExpiredError() from None
        old_session = await self.sessions.get_by_jti(jti)
        if not old_session or old_session.revoked_at is not None:
            raise SessionRevokedError()
        if old_session.expires_at <= datetime.now(UTC):
            raise SessionExpiredError()
        user = await self.users.get_by_id(user_id)
        if not user or not user.is_active:
            raise SessionExpiredError()
        await self.sessions.revoke(old_session, datetime.now(UTC))
        result = await self.issue_session(user, user_agent)
        await self.session.commit()
        return result

    async def logout(self, token: str | None):
        if token:
            try:
                payload = decode_token(token, "refresh")
                item = await self.sessions.get_by_jti(payload["jti"])
                if item and item.revoked_at is None:
                    await self.sessions.revoke(item, datetime.now(UTC))
                    await self.session.commit()
            except (jwt.PyJWTError, KeyError):
                pass
