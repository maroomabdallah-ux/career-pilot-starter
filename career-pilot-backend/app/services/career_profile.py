from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    CareerProfileAlreadyExistsError,
    CareerProfileNotFoundError,
    UserNotFoundError,
)
from app.repositories.career_profile import CareerProfileRepository
from app.repositories.user import UserRepository
from app.schemas.career_profile import CareerProfileCreate, CareerProfileUpdate


class CareerProfileService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = CareerProfileRepository(session)

    async def get_profile(self, profile_id: UUID):
        item = await self.repository.get_by_id(profile_id)
        if not item:
            raise CareerProfileNotFoundError()
        return item

    async def get_profile_by_user(self, user_id: UUID):
        item = await self.repository.get_by_user_id(user_id)
        if not item:
            raise CareerProfileNotFoundError()
        return item

    async def create_profile(self, data: CareerProfileCreate):
        if not await UserRepository(self.session).get_by_id(data.user_id):
            raise UserNotFoundError()
        if await self.repository.get_by_user_id(data.user_id):
            raise CareerProfileAlreadyExistsError()
        try:
            item = await self.repository.create(data)
            await self.session.commit()
            return await self.get_profile(item.id)
        except IntegrityError:
            await self.session.rollback()
            raise CareerProfileAlreadyExistsError() from None

    async def update_profile(self, profile_id: UUID, data: CareerProfileUpdate):
        item = await self.repository.update(await self.get_profile(profile_id), data)
        await self.session.commit()
        return await self.get_profile(item.id)

    async def delete_profile(self, profile_id: UUID):
        await self.repository.delete(await self.get_profile(profile_id))
        await self.session.commit()
