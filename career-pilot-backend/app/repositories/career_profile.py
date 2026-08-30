from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.career_profile import CareerProfile
from app.repositories.base import schema_values
from app.schemas.career_profile import CareerProfileCreate, CareerProfileUpdate


def _full_query():
    return select(CareerProfile).options(
        selectinload(CareerProfile.education),
        selectinload(CareerProfile.experiences),
        selectinload(CareerProfile.projects),
        selectinload(CareerProfile.skills),
    )


class CareerProfileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, profile_id: UUID) -> CareerProfile | None:
        return await self.session.scalar(_full_query().where(CareerProfile.id == profile_id))

    async def get_by_user_id(self, user_id: UUID) -> CareerProfile | None:
        return await self.session.scalar(_full_query().where(CareerProfile.user_id == user_id))

    async def create(self, data: CareerProfileCreate) -> CareerProfile:
        profile = CareerProfile(**schema_values(data))
        self.session.add(profile)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def update(self, profile: CareerProfile, data: CareerProfileUpdate) -> CareerProfile:
        for field, value in schema_values(data, exclude_unset=True).items():
            setattr(profile, field, value)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def delete(self, profile: CareerProfile) -> None:
        await self.session.delete(profile)
        await self.session.flush()
