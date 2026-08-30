from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CareerProfileNotFoundError
from app.repositories.career_profile import CareerProfileRepository


class ChildService:
    not_found_error: type[Exception]

    def __init__(self, session: AsyncSession, repository: Any):
        self.session, self.repository = session, repository

    async def get(self, item_id: UUID):
        item = await self.repository.get_by_id(item_id)
        if not item:
            raise self.not_found_error()
        return item

    async def list(self, profile_id: UUID):
        if not await CareerProfileRepository(self.session).get_by_id(profile_id):
            raise CareerProfileNotFoundError()
        return await self.repository.list_by_profile(profile_id)

    async def create(self, profile_id: UUID, data: BaseModel):
        if not await CareerProfileRepository(self.session).get_by_id(profile_id):
            raise CareerProfileNotFoundError()
        item = await self.repository.create(profile_id, data)
        await self.session.commit()
        return item

    async def update(self, item_id: UUID, data: BaseModel):
        item = await self.get(item_id)
        item = await self.repository.update(item, data)
        await self.session.commit()
        return item

    async def delete(self, item_id: UUID) -> None:
        await self.repository.delete(await self.get(item_id))
        await self.session.commit()
