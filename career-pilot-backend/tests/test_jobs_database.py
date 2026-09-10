import os
from uuid import uuid4

import pytest
from sqlalchemy import delete

from app.core.exceptions import NotFoundError
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.schemas.application import ApplicationPrepare
from app.schemas.job import JobResult
from app.services.applications import ApplicationService
from app.services.jobs import SavedJobService

pytestmark = pytest.mark.skipif(not os.getenv("RUN_DATABASE_TESTS"), reason="requires PostgreSQL")


@pytest.mark.asyncio
async def test_saved_jobs_history_persist_and_are_user_scoped():
    marker = uuid4().hex
    async with AsyncSessionLocal() as session:
        a = User(email=f"job-a-{marker}@example.com", first_name="A", last_name="U")
        b = User(email=f"job-b-{marker}@example.com", first_name="B", last_name="U")
        session.add_all([a, b])
        await session.commit()
        item = await SavedJobService(session, a.id).save(
            JobResult(
                external_id="real-1",
                source="TestATS",
                source_url="https://example.com/1",
                title="Backend Developer",
                company="Acme",
                workplace_type="remote",
                apply_url="https://example.com/1",
                retrieved_at="2026-09-06T00:00:00Z",
            )
        )
        assert len(await SavedJobService(session, a.id).list()) == 1
        assert await SavedJobService(session, b.id).list() == []
        with pytest.raises(NotFoundError):
            await SavedJobService(session, b.id).unsave(item.id)
        await SavedJobService(session, a.id).unsave(item.id)
        assert await SavedJobService(session, a.id).list() == []
        await session.execute(delete(User).where(User.id.in_([a.id, b.id])))
        await session.commit()


@pytest.mark.asyncio
async def test_application_can_be_created_listed_and_prepared():
    marker = uuid4().hex
    async with AsyncSessionLocal() as session:
        user = User(
            email=f"application-{marker}@example.com",
            first_name="Application",
            last_name="Tester",
        )
        session.add(user)
        await session.commit()
        service = ApplicationService(session, user)
        created = await service.create(
            JobResult(
                external_id=f"application-{marker}",
                source="TestATS",
                source_url="https://example.com/job",
                title="Backend Developer",
                company="Acme",
                workplace_type="remote",
                apply_url="https://example.com/apply",
                retrieved_at="2026-09-10T00:00:00Z",
            )
        )

        assert [item.id for item in await service.list()] == [created.id]
        prepared = await service.prepare(
            created.id,
            ApplicationPrepare(
                version=created.version,
                cover_letter="Prepared for review.",
                application_url="https://example.com/apply",
            ),
        )
        assert prepared.status == "ready_for_review"
        assert prepared.cover_letter == "Prepared for review."
        assert prepared.profile_snapshot["email"] == user.email

        await session.delete(user)
        await session.commit()
