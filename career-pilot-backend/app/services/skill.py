from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import DuplicateSkillError, SkillNotFoundError
from app.repositories.skill import SkillRepository
from app.schemas.skill import SkillCreate, SkillUpdate
from app.services.base import ChildService


class SkillService(ChildService):
    not_found_error = SkillNotFoundError

    def __init__(self, session: AsyncSession):
        super().__init__(session, SkillRepository(session))

    get_skill = ChildService.get
    list_skills = ChildService.list
    delete_skill = ChildService.delete

    async def create_skill(self, profile_id: UUID, data: SkillCreate):
        if await self.repository.get_by_profile_and_name(profile_id, data.name):
            raise DuplicateSkillError()
        try:
            return await self.create(profile_id, data)
        except IntegrityError:
            await self.session.rollback()
            raise DuplicateSkillError() from None

    async def update_skill(self, skill_id: UUID, data: SkillUpdate):
        skill = await self.get(skill_id)
        if data.name is not None:
            duplicate = await self.repository.get_by_profile_and_name(
                skill.career_profile_id, data.name
            )
            if duplicate and duplicate.id != skill.id:
                raise DuplicateSkillError()
        try:
            return await self.update(skill_id, data)
        except IntegrityError:
            await self.session.rollback()
            raise DuplicateSkillError() from None
