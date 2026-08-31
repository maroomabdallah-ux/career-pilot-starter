from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import CareerProfileNotFoundError, ProfileAccessDeniedError
from app.models.user import User
from app.repositories.career_profile import CareerProfileRepository
from app.schemas.career_profile import CareerProfileCreate, CareerProfileUpdate
from app.services.career_profile import CareerProfileService


class MeService:
    def __init__(self, session: AsyncSession, user: User):
        self.session, self.user = session, user
        self.profiles = CareerProfileRepository(session)

    async def profile(self):
        profile = await self.profiles.get_by_user_id(self.user.id)
        if not profile:
            raise CareerProfileNotFoundError()
        return profile

    async def create_profile(self, data: CareerProfileUpdate):
        payload = CareerProfileCreate(user_id=self.user.id, **data.model_dump(exclude_unset=True))
        return await CareerProfileService(self.session).create_profile(payload)

    async def update_profile(self, data: CareerProfileUpdate):
        return await CareerProfileService(self.session).update_profile(
            (await self.profile()).id, data
        )

    async def list_children(self, service: Any, method: str):
        return await getattr(service, method)((await self.profile()).id)

    async def create_child(self, service: Any, method: str, data: Any):
        return await getattr(service, method)((await self.profile()).id, data)

    async def owned_child(self, service: Any, get_method: str, item_id: UUID):
        item = await getattr(service, get_method)(item_id)
        profile = await self.profile()
        if item.career_profile_id != profile.id:
            raise ProfileAccessDeniedError()
        return item

    async def update_child(
        self, service: Any, get_method: str, update_method: str, item_id: UUID, data: Any
    ):
        await self.owned_child(service, get_method, item_id)
        return await getattr(service, update_method)(item_id, data)

    async def delete_child(self, service: Any, get_method: str, delete_method: str, item_id: UUID):
        await self.owned_child(service, get_method, item_id)
        await getattr(service, delete_method)(item_id)

    async def complete_onboarding(self):
        await self.profile()
        self.user.onboarding_completed = True
        await self.session.commit()
        await self.session.refresh(self.user)
        return self.user
