from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UserAlreadyExistsError, UserNotFoundError
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repository = UserRepository(session)

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    async def get_user(self, user_id: UUID):
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise UserNotFoundError()
        return user

    async def get_user_by_email(self, email: str):
        user = await self.repository.get_by_email(self.normalize_email(email))
        if not user:
            raise UserNotFoundError()
        return user

    async def create_user(self, data: UserCreate):
        email = self.normalize_email(str(data.email))
        if await self.repository.get_by_email(email):
            raise UserAlreadyExistsError()
        normalized = data.model_copy(update={"email": email})
        try:
            user = await self.repository.create(normalized)
            await self.session.commit()
            return user
        except IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsError() from None

    async def update_user(self, user_id: UUID, data: UserUpdate):
        user = await self.get_user(user_id)
        if data.email is not None:
            email = self.normalize_email(str(data.email))
            existing = await self.repository.get_by_email(email)
            if existing and existing.id != user.id:
                raise UserAlreadyExistsError()
            data = data.model_copy(update={"email": email})
        try:
            user = await self.repository.update(user, data)
            await self.session.commit()
            return user
        except IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsError() from None

    async def delete_user(self, user_id: UUID):
        await self.repository.delete(await self.get_user(user_id))
        await self.session.commit()
