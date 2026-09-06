from abc import ABC, abstractmethod

from app.schemas.job import JobResult, JobSearchCriteria


class JobSourceAdapter(ABC):
    name: str
    authority: int = 10

    @abstractmethod
    async def search(self, criteria: JobSearchCriteria) -> list[JobResult]:
        raise NotImplementedError
