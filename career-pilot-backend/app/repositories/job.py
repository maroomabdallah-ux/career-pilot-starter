from uuid import UUID

from sqlalchemy import select

from app.models.job import JobSearchHistory, SavedJob


class JobRepository:
    def __init__(self, session):
        self.session = session

    async def list_saved(self, user_id: UUID):
        return list(
            await self.session.scalars(
                select(SavedJob)
                .where(SavedJob.user_id == user_id)
                .order_by(SavedJob.saved_at.desc())
            )
        )

    async def get_saved(self, user_id: UUID, item_id: UUID):
        return await self.session.scalar(
            select(SavedJob).where(SavedJob.id == item_id, SavedJob.user_id == user_id)
        )

    async def find_saved(self, user_id: UUID, source: str, external_id: str):
        return await self.session.scalar(
            select(SavedJob).where(
                SavedJob.user_id == user_id,
                SavedJob.source == source,
                SavedJob.external_job_id == external_id,
            )
        )

    async def add(self, item):
        self.session.add(item)
        await self.session.commit()
        await self.session.refresh(item)
        return item

    async def delete(self, item):
        await self.session.delete(item)
        await self.session.commit()

    async def history(self, user_id: UUID, limit: int = 20):
        return list(
            await self.session.scalars(
                select(JobSearchHistory)
                .where(JobSearchHistory.user_id == user_id)
                .order_by(JobSearchHistory.created_at.desc())
                .limit(limit)
            )
        )
