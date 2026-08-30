from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ExperienceNotFoundError
from app.repositories.experience import ExperienceRepository
from app.services.base import ChildService


class ExperienceService(ChildService):
    not_found_error = ExperienceNotFoundError

    def __init__(self, session: AsyncSession):
        super().__init__(session, ExperienceRepository(session))

    get_experience = ChildService.get
    list_experiences = ChildService.list
    create_experience = ChildService.create
    update_experience = ChildService.update
    delete_experience = ChildService.delete
