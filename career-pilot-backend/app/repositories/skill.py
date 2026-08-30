from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skill import Skill
from app.repositories.base import ChildRepository


class SkillRepository(ChildRepository[Skill]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Skill)

    async def get_by_profile_and_name(self, profile_id: UUID, name: str) -> Skill | None:
        return await self.session.scalar(
            select(Skill).where(
                Skill.career_profile_id == profile_id, func.lower(Skill.name) == name.lower()
            )
        )
