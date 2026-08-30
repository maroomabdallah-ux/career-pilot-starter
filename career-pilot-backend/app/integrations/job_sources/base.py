from abc import ABC, abstractmethod


class JobSourceAdapter(ABC):
    @abstractmethod
    async def search(self, query: str, location: str | None = None):
        raise NotImplementedError
