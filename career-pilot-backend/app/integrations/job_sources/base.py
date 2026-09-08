from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.schemas.job import JobResult, JobSearchCriteria


@dataclass(slots=True)
class JobProviderResult:
    jobs: list[JobResult]
    next_page_token: str | None = None


class JobProvider(ABC):
    name: str
    authority: int = 10

    @abstractmethod
    async def search(self, criteria: JobSearchCriteria) -> list[JobResult] | JobProviderResult:
        raise NotImplementedError


class JobSourceAdapter(JobProvider):
    """Backward-compatible base for the existing job-source integrations."""
