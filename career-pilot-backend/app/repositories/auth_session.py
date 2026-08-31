from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth_session import AuthSession


class AuthSessionRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_jti(self, jti: str) -> AuthSession | None:
        return await self.session.scalar(
            select(AuthSession).where(AuthSession.refresh_token_jti == jti)
        )

    async def create(self, **values) -> AuthSession:
        item = AuthSession(**values)
        self.session.add(item)
        await self.session.flush()
        return item

    async def revoke(self, item: AuthSession, revoked_at: datetime) -> None:
        item.revoked_at = revoked_at
        await self.session.flush()
