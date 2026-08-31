import asyncio
from time import monotonic

import httpx


class UniversityProviderError(Exception):
    pass


class UniversityReferenceService:
    provider_url = "https://universities.hipolabs.com/search"
    _cache: dict[str, tuple[float, list[dict]]] = {}
    _lock = asyncio.Lock()

    async def search(self, query: str, country: str | None, limit: int = 25) -> list[dict]:
        key = f"{query.casefold()}:{(country or '').casefold()}:{limit}"
        cached = self._cache.get(key)
        if cached and cached[0] > monotonic():
            return cached[1]
        params = {"name": query}
        if country:
            params["country"] = country
        try:
            async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
                response = await client.get(self.provider_url, params=params)
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise UniversityProviderError() from exc
        results = [
            {
                "name": item.get("name", ""),
                "country": item.get("country", ""),
                "country_code": item.get("alpha_two_code", ""),
                "domain": (item.get("domains") or [None])[0],
            }
            for item in payload
            if item.get("name")
        ][:limit]
        async with self._lock:
            self._cache[key] = (monotonic() + 3600, results)
            if len(self._cache) > 500:
                self._cache = dict(list(self._cache.items())[-250:])
        return results
