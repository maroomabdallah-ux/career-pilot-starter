from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_user(self, user_id: UUID):
        return list(
            await self.session.scalars(
                select(Resume)
                .where(Resume.user_id == user_id)
                .order_by(Resume.updated_at.desc())
            )
        )

    async def get_for_user(self, user_id: UUID, resume_id: UUID):
        return await self.session.scalar(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )

    async def create(self, resume: Resume):
        self.session.add(resume)
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def next_version(self, user_id: UUID) -> int:
        current = await self.session.scalar(
            select(func.max(Resume.version)).where(Resume.user_id == user_id)
        )
        return (current or 0) + 1

    async def save(self, resume: Resume):
        await self.session.commit()
        await self.session.refresh(resume)
        return resume

    async def delete(self, resume: Resume):
        await self.session.delete(resume)
        await self.session.commit()
