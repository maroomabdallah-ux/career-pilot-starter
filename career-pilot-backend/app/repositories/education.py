from sqlalchemy.ext.asyncio import AsyncSession

from app.models.education import Education
from app.repositories.base import ChildRepository


class EducationRepository(ChildRepository[Education]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Education)
