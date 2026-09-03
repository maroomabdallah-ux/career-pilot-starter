from uuid import UUID

from app.models.resume import Resume
from app.repositories.resume import ResumeRepository


class ResumeService:
    def __init__(self, session, user_id: UUID):
        self.repository = ResumeRepository(session)
        self.user_id = user_id

    async def list(self):
        return await self.repository.list_for_user(self.user_id)

    async def get(self, resume_id):
        item = await self.repository.get_for_user(self.user_id, resume_id)
        if not item:
            raise ValueError("Resume not found")
        return item

    async def create(self, title, language, content, template_id="ats_classic"):
        from app.services.resume_templates import get_template

        template_id = get_template(template_id)["id"]
        return await self.repository.create(
            Resume(
                user_id=self.user_id,
                title=title,
                language=language,
                content=content,
                template_id=template_id,
                version=await self.repository.next_version(self.user_id),
            )
        )

    async def update(self, resume_id, data):
        item = await self.get(resume_id)
        if item.status == "approved":
            raise ValueError(
                "Approved resumes are immutable. Create a new version to make changes."
            )
        for key, value in data.model_dump(exclude_unset=True).items():
            if key == "template_id":
                from app.services.resume_templates import get_template

                value = get_template(value)["id"]
            if key == "content" and hasattr(value, "model_dump"):
                value = value.model_dump(mode="json")
            setattr(item, key, value)
        return await self.repository.save(item)

    async def transition(self, resume_id, status):
        item = await self.get(resume_id)
        allowed = {
            "draft": {"review", "archived"},
            "review": {"draft", "approved", "archived"},
            "approved": {"archived"},
            "archived": set(),
        }
        if status not in allowed[item.status]:
            raise ValueError(f"Cannot move resume from {item.status} to {status}")
        item.status = status
        return await self.repository.save(item)

    async def delete(self, resume_id):
        await self.repository.delete(await self.get(resume_id))
