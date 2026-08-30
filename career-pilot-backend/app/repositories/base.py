from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


def schema_values(data: BaseModel, *, exclude_unset: bool = False) -> dict[str, Any]:
    values = data.model_dump(exclude_unset=exclude_unset)
    return {
        key: str(value) if hasattr(value, "unicode_string") else value
        for key, value in values.items()
    }


class ChildRepository(Generic[ModelT]):
    def __init__(self, session: AsyncSession, model: type[ModelT]):
        self.session = session
        self.model = model

    async def get_by_id(self, item_id: UUID) -> ModelT | None:
        return await self.session.get(self.model, item_id)

    async def list_by_profile(self, profile_id: UUID) -> list[ModelT]:
        result = await self.session.scalars(
            select(self.model).where(self.model.career_profile_id == profile_id)
        )
        return list(result.all())

    async def create(self, profile_id: UUID, data: BaseModel) -> ModelT:
        item = self.model(career_profile_id=profile_id, **schema_values(data))
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def update(self, item: ModelT, data: BaseModel) -> ModelT:
        for field, value in schema_values(data, exclude_unset=True).items():
            setattr(item, field, value)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def delete(self, item: ModelT) -> None:
        await self.session.delete(item)
        await self.session.flush()
