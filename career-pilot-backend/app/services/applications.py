from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.exceptions import ConflictError, NotFoundError
from app.models.application import ApplicationEvent, JobApplication
from app.repositories.career_profile import CareerProfileRepository
from app.repositories.resume import ResumeRepository
from app.schemas.application import ApplicationResponse
from app.services.jobs import SavedJobService


class ApplicationService:
    def __init__(self, session, user):
        self.session, self.user = session, user

    async def get(self, application_id, *, lock=False):
        query = select(JobApplication).where(
            JobApplication.id == application_id, JobApplication.user_id == self.user.id
        )
        if lock:
            query = query.with_for_update().execution_options(populate_existing=True)
        item = await self.session.scalar(query)
        if not item:
            raise NotFoundError("Application not found")
        return item

    async def response(self, item):
        result = ApplicationResponse.model_validate(item)
        events = await self.session.scalars(
            select(ApplicationEvent)
            .where(ApplicationEvent.application_id == item.id)
            .order_by(ApplicationEvent.created_at, ApplicationEvent.id)
        )
        result.events = list(events)
        return result

    async def list(self):
        rows = await self.session.scalars(
            select(JobApplication)
            .where(JobApplication.user_id == self.user.id)
            .order_by(JobApplication.updated_at.desc())
        )
        return [ApplicationResponse.model_validate(item) for item in rows]

    def event(self, item, kind, message):
        self.session.add(ApplicationEvent(application_id=item.id, kind=kind, message=message))

    async def create(self, job):
        saved = await SavedJobService(self.session, self.user.id).save(job)
        inserted = await self.session.scalar(
            insert(JobApplication)
            .values(
                user_id=self.user.id,
                saved_job_id=saved.id,
                source=job.source,
                external_job_id=job.external_id,
                job_snapshot=job.model_dump(mode="json"),
                application_url=str(job.apply_url),
            )
            .on_conflict_do_nothing(constraint="uq_application_user_job")
            .returning(JobApplication.id)
        )
        item = await self.session.scalar(
            select(JobApplication).where(
                JobApplication.user_id == self.user.id,
                JobApplication.source == job.source,
                JobApplication.external_job_id == job.external_id,
            )
        )
        if inserted:
            self.event(item, "draft", "Application draft created from the selected job.")
        await self.session.commit()
        await self.session.refresh(item)
        return await self.response(item)

    @staticmethod
    def check_version(item, version):
        if item.version != version:
            raise ConflictError("This application changed. Refresh it before continuing.")

    async def prepare(self, application_id, data):
        item = await self.get(application_id, lock=True)
        self.check_version(item, data.version)
        if item.status not in {"draft", "ready_for_review"}:
            raise ConflictError("This application has already been approved or tracked.")
        resume = None
        if data.resume_id:
            resume = await ResumeRepository(self.session).get_for_user(self.user.id, data.resume_id)
            if not resume or resume.status == "archived":
                raise NotFoundError("Selected resume is unavailable")
        url = str(data.application_url or item.application_url)
        allowed = {item.job_snapshot.get("apply_url"), item.application_url}
        allowed.update(x.get("link") for x in item.job_snapshot.get("apply_options", []))
        if url not in allowed:
            raise ConflictError("Choose an application link supplied by this job.")
        profile = await CareerProfileRepository(self.session).get_by_user_id(self.user.id)
        item.profile_snapshot = {
            "name": f"{self.user.first_name} {self.user.last_name}",
            "email": self.user.email,
            "phone": profile.phone if profile else None,
            "location": ", ".join(x for x in (profile.city, profile.country) if x)
            if profile
            else "",
        }
        item.resume_id = resume.id if resume else None
        item.resume_snapshot = (
            {"title": resume.title, "content": resume.content, "template_id": resume.template_id}
            if resume
            else {}
        )
        item.cover_letter, item.answers = data.cover_letter, data.answers
        item.application_url = url
        item.status, item.version = "ready_for_review", item.version + 1
        self.event(
            item, "prepared", "Application materials prepared for review; nothing submitted."
        )
        await self.session.commit()
        await self.session.refresh(item)
        return await self.response(item)

    async def approve(self, application_id, data):
        item = await self.get(application_id, lock=True)
        # A duplicate approval cannot create another action or event, even with a new key.
        if item.approved_at:
            return await self.response(item)
        self.check_version(item, data.version)
        if not data.approved or item.status != "ready_for_review":
            raise ConflictError("Prepare and review this application before approving it.")
        item.approved_at = datetime.now(UTC)
        item.status, item.version = "external_application", item.version + 1
        self.event(item, "approved", "User explicitly approved the reviewed application materials.")
        self.event(
            item,
            "external_handoff",
            "External application link made available; submission is unverified.",
        )
        await self.session.commit()
        await self.session.refresh(item)
        return await self.response(item)

    async def track(self, application_id, data):
        item = await self.get(application_id, lock=True)
        if item.status == data.status:
            return await self.response(item)
        self.check_version(item, data.version)
        allowed = {
            "draft": {"withdrawn"},
            "ready_for_review": {"withdrawn"},
            "external_application": {"submitted_externally", "withdrawn"},
            "submitted_externally": {"interview", "offer", "rejected", "withdrawn"},
            "interview": {"offer", "rejected", "withdrawn"},
            "offer": {"withdrawn"},
        }
        if data.status not in allowed.get(item.status, set()):
            raise ConflictError("That status transition is not available.")
        if data.status == "submitted_externally":
            item.applied_at = datetime.now(UTC)
            item.submission_evidence = "user_reported"
        item.status, item.notes = data.status, data.notes
        item.version += 1
        self.event(
            item,
            data.status,
            "User reported: "
            + data.status.replace("_", " ")
            + (f". {data.notes}" if data.notes else ""),
        )
        await self.session.commit()
        await self.session.refresh(item)
        return await self.response(item)
