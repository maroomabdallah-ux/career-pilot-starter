from __future__ import annotations

from functools import lru_cache
from uuid import UUID

from langchain_openai import OpenAIEmbeddings
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.career_knowledge import CareerKnowledgeChunk, CareerKnowledgeDocument
from app.repositories.career_knowledge import CareerKnowledgeRepository


class CareerKnowledgeConfigurationError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_career_embeddings() -> OpenAIEmbeddings:
    if not settings.OPENAI_API_KEY:
        raise CareerKnowledgeConfigurationError(
            "OPENAI_API_KEY is required for career knowledge retrieval."
        )
    return OpenAIEmbeddings(model=settings.OPENAI_EMBEDDING_MODEL, api_key=settings.OPENAI_API_KEY)


def chunk_text(content: str, size: int = 2800, overlap: int = 300) -> list[str]:
    """Character approximation of 400–800 tokens, preserving paragraph boundaries when possible."""
    clean = "\n".join(line.strip() for line in content.splitlines() if line.strip())
    if not clean:
        return []
    chunks, start = [], 0
    while start < len(clean):
        end = min(len(clean), start + size)
        if end < len(clean):
            boundary = clean.rfind("\n", start, end)
            end = boundary if boundary > start + size // 2 else end
        chunks.append(clean[start:end].strip())
        start = end if end == len(clean) else max(end - overlap, start + 1)
    return chunks


class CareerKnowledgeService:
    def __init__(self, session: AsyncSession, user_id: UUID):
        self.session = session
        self.user_id = user_id
        self.repository = CareerKnowledgeRepository(session)

    async def ingest_document(
        self,
        *,
        source_type: str,
        title: str,
        content: str,
        source_reference: str | None = None,
        metadata: dict | None = None,
    ) -> CareerKnowledgeDocument:
        chunks = chunk_text(content)
        if not chunks:
            raise ValueError("Career knowledge content cannot be empty.")
        vectors = await get_career_embeddings().aembed_documents(chunks)
        document = await self.repository.create_document(
            CareerKnowledgeDocument(
                user_id=self.user_id,
                source_type=source_type,
                title=title,
                source_reference=source_reference,
            )
        )
        await self.repository.create_chunks(
            [
                CareerKnowledgeChunk(
                    document_id=document.id,
                    user_id=self.user_id,
                    content=chunk,
                    embedding=vector,
                    metadata_json={
                        **(metadata or {}),
                        "source_type": source_type,
                        "document_title": title,
                    },
                    chunk_index=index,
                )
                for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
            ]
        )
        await self.session.commit()
        return document

    async def delete_document(self, document_id: UUID) -> bool:
        deleted = await self.repository.delete_document(self.user_id, document_id)
        await self.session.commit()
        return deleted

    async def retrieve(
        self,
        query: str,
        *,
        domain: str | None = None,
        company: str | None = None,
        project: str | None = None,
        limit: int = 5,
    ) -> list[CareerKnowledgeChunk]:
        embedding = await get_career_embeddings().aembed_query(query)
        return await self.repository.similarity_search(
            self.user_id,
            embedding,
            min(max(limit, 1), 6),
            domain=domain,
            company=company,
            project=project,
        )
