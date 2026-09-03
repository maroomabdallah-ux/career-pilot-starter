from uuid import UUID

from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_knowledge import CareerKnowledgeChunk, CareerKnowledgeDocument


class CareerKnowledgeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_document(self, document: CareerKnowledgeDocument) -> CareerKnowledgeDocument:
        self.session.add(document)
        await self.session.flush()
        return document

    async def create_chunks(self, chunks: list[CareerKnowledgeChunk]) -> None:
        self.session.add_all(chunks)
        await self.session.flush()

    async def delete_document(self, user_id: UUID, document_id: UUID) -> bool:
        result = await self.session.execute(
            delete(CareerKnowledgeDocument).where(
                CareerKnowledgeDocument.id == document_id,
                CareerKnowledgeDocument.user_id == user_id,
            )
        )
        return bool(result.rowcount)

    async def similarity_search(
        self,
        user_id: UUID,
        embedding: list[float],
        limit: int,
        *,
        domain: str | None = None,
        company: str | None = None,
        project: str | None = None,
    ) -> list[CareerKnowledgeChunk]:
        filters = []
        params = {
            "user_id": user_id,
            "embedding": "[" + ",".join(map(str, embedding)) + "]",
            "limit": limit,
        }
        for key, value in (("domain", domain), ("company", company), ("project", project)):
            if value:
                filters.append(f"AND (metadata_json ->> '{key}') = :{key}")
                params[key] = value
        statement = text(
            "SELECT * FROM career_knowledge_chunks "
            "WHERE user_id = :user_id " + " ".join(filters) + " "
            "ORDER BY embedding <=> CAST(:embedding AS vector) LIMIT :limit"
        )
        result = await self.session.scalars(
            select(CareerKnowledgeChunk).from_statement(statement).params(**params)
        )
        return list(result)
