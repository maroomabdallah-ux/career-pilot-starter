from sqlalchemy.ext.asyncio import AsyncSession

from app.models.experience import Experience
from app.repositories.base import ChildRepository


class ExperienceRepository(ChildRepository[Experience]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Experience)
