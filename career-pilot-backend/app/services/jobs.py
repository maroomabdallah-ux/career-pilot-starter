from uuid import UUID

from sqlalchemy.dialects.postgresql import insert

from app.core.exceptions import NotFoundError
from app.models.job import JobSearchHistory, SavedJob
from app.repositories.job import JobRepository
from app.schemas.job import JobResult, JobSearchCriteria


class SavedJobService:
    def __init__(self, session, user_id: UUID):
        self.repository = JobRepository(session)
        self.user_id = user_id

    async def list(self):
        return await self.repository.list_saved(self.user_id)

    async def save(self, job: JobResult):
        data = job.model_dump(mode="json")
        statement = (
            insert(SavedJob)
            .values(
                user_id=self.user_id,
                source=job.source,
                external_job_id=job.external_id,
                title=job.title,
                company=job.company,
                location=job.location,
                workplace_type=job.workplace_type,
                employment_type=job.employment_type,
                apply_url=str(job.apply_url),
                source_url=str(job.source_url),
                snapshot=data,
            )
            .on_conflict_do_nothing(index_elements=["user_id", "source", "external_job_id"])
        )
        session = self.repository.session
        await session.execute(statement)
        await session.commit()
        return await self.repository.find_saved(self.user_id, job.source, job.external_id)

    async def unsave(self, item_id: UUID):
        item = await self.repository.get_saved(self.user_id, item_id)
        if not item:
            raise NotFoundError("Saved job not found")
        await self.repository.delete(item)

    async def record_search(self, criteria: JobSearchCriteria, result_count, sources, failures):
        return await self.repository.add(
            JobSearchHistory(
                user_id=self.user_id,
                criteria=criteria.model_dump(mode="json"),
                result_count=result_count,
                sources=sources,
                source_failures=failures,
            )
        )

    async def history(self):
        return await self.repository.history(self.user_id)
