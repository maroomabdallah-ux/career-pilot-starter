from copy import deepcopy
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.exceptions import ConflictError, NotFoundError
from app.models.application import ApplicationEvent, JobApplication
from app.models.resume import Resume
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

    async def tailor(self, application_id, data):
        item = await self.get(application_id, lock=True)
        self.check_version(item, data.version)
        if item.status not in {"draft", "ready_for_review"}:
            raise ConflictError("Approved applications cannot be re-tailored.")
        master = await ResumeRepository(self.session).get_for_user(self.user.id, data.resume_id)
        if not master or master.status == "archived":
            raise NotFoundError("Selected resume is unavailable")
        content = deepcopy(master.content)
        job_text = " ".join(
            [item.job_snapshot.get("title", ""), item.job_snapshot.get("description", "")]
        ).casefold()
        for group in content.get("skill_groups", []):
            group["items"] = sorted(
                group.get("items", []), key=lambda skill: skill.casefold() not in job_text
            )
        content["section_order"] = [
            section
            for section in ("summary", "skills", "experience", "projects", "education")
            if section in content.get("section_order", []) or content.get(section)
        ]
        version = await ResumeRepository(self.session).next_version(self.user.id)
        tailored = Resume(
            user_id=self.user.id,
            title=f"{master.title} · {item.job_snapshot.get('company', 'Targeted')}",
            document_type=master.document_type,
            version=version,
            status="draft",
            template_id=master.template_id,
            language=master.language,
            content=content,
            design=deepcopy(master.design),
        )
        self.session.add(tailored)
        await self.session.flush()
        item.resume_id = tailored.id
        item.resume_snapshot = {
            "title": tailored.title,
            "content": content,
            "template_id": tailored.template_id,
            "tailored_from": str(master.id),
        }
        item.version += 1
        self.event(item, "tailored", "A separate job-specific resume draft was created.")
        await self.session.commit()
        await self.session.refresh(item)
        return await self.response(item)

    async def generate_preparation(self, application_id, data):
        item = await self.get(application_id, lock=True)
        self.check_version(item, data.version)
        job = item.job_snapshot
        profile = await CareerProfileRepository(self.session).get_by_user_id(self.user.id)
        missing = []
        if not item.resume_id:
            missing.append("Which resume would you like to use?")
        if not profile or not profile.professional_summary:
            missing.append("What relevant achievement should the cover letter emphasize?")
        facts = list((job.get("matched_skills") or [])[:3])
        evidence = f" My relevant experience includes {', '.join(facts)}." if facts else ""
        item.cover_letter = (
            f"Dear {job.get('company', 'Hiring Team')} Hiring Team,\n\n"
            f"I am applying for the {job.get('title', 'open')} role.{evidence} "
            "I would welcome the opportunity to discuss how my documented "
            "experience can contribute.\n\n"
            f"Sincerely,\n{self.user.first_name} {self.user.last_name}"
        )
        item.answers = [
            {"question": question, "answer": data.user_context.get(question, "")}
            for question in missing
            if data.user_context.get(question)
        ]
        item.version += 1
        self.event(item, "generated", "A grounded application preparation draft was generated.")
        await self.session.commit()
        await self.session.refresh(item)
        return await self.response(item), [q for q in missing if not data.user_context.get(q)]

    async def interview_kit(self, application_id):
        item = await self.get(application_id)
        job = item.job_snapshot
        skills = (job.get("skills") or [])[:5]
        return {
            "questions": [
                f"Why are you interested in the {job.get('title')} role at {job.get('company')}?",
                "Tell me about a relevant challenge you solved and the measurable result.",
                "Which requirement would stretch you most, and how would you close the gap?",
            ],
            "star_prompts": [
                "Situation and context",
                "Your specific task",
                "Actions you took",
                "Result and learning",
            ],
            "technical_topics": skills,
            "grounding_note": (
                "Questions use the saved job snapshot; answers must use user-confirmed facts."
            ),
        }

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
