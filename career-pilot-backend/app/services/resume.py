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

    async def create(self, title, language, content):
        return await self.repository.create(
            Resume(user_id=self.user_id, title=title, language=language, content=content)
        )

    async def update(self, resume_id, data):
        item = await self.get(resume_id)
        for key, value in data.model_dump(exclude_unset=True).items():
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
