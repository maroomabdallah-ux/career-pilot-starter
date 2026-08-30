from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EducationNotFoundError
from app.repositories.education import EducationRepository
from app.services.base import ChildService


class EducationService(ChildService):
    not_found_error = EducationNotFoundError

    def __init__(self, session: AsyncSession):
        super().__init__(session, EducationRepository(session))

    get_education = ChildService.get
    list_education = ChildService.list
    create_education = ChildService.create
    update_education = ChildService.update
    delete_education = ChildService.delete
