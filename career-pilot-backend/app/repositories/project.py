from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.base import ChildRepository


class ProjectRepository(ChildRepository[Project]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, Project)
