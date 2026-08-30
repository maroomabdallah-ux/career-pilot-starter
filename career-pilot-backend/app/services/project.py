from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProjectNotFoundError
from app.repositories.project import ProjectRepository
from app.services.base import ChildService


class ProjectService(ChildService):
    not_found_error = ProjectNotFoundError

    def __init__(self, session: AsyncSession):
        super().__init__(session, ProjectRepository(session))

    get_project = ChildService.get
    list_projects = ChildService.list
    create_project = ChildService.create
    update_project = ChildService.update
    delete_project = ChildService.delete
