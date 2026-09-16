from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import UTC, datetime, timedelta
from html import unescape

from app.core.config import settings
from app.integrations.job_sources import (
    JobProvider,
    JobProviderResult,
    SerpApiJobProvider,
)
from app.schemas.job import JobResult, JobSearchCriteria, JobSearchResponse

logger = logging.getLogger(__name__)
TOKEN = re.compile(r"[a-z0-9+#.]{2,}", re.I)
HTML = re.compile(r"<[^>]+>")


class JobSearchService:
    def __init__(self, sources: list[JobProvider] | None = None, cache_ttl: int = 3600):
        self.sources = sources if sources is not None else self._configured_sources()
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, JobSearchResponse]] = {}
        self._inflight: dict[str, asyncio.Task] = {}
        self._details: dict[tuple[str, str], JobResult] = {}

    @staticmethod
    def _configured_sources() -> list[JobProvider]:
        if settings.SERPAPI_API_KEY:
            return [SerpApiJobProvider(settings.SERPAPI_API_KEY)]
        logger.warning("Google Jobs unavailable: SERPAPI_API_KEY not configured")
        return []

    async def search(
        self, criteria: JobSearchCriteria, supplementary_queries: list[str] | None = None
    ) -> JobSearchResponse:
        queries = tuple(dict.fromkeys(
            query.strip() for query in (supplementary_queries or []) if query.strip()
        ))[:3] if not criteria.query else ()
        key = criteria.model_dump_json() + "|" + "|".join(queries)
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < self.cache_ttl:
            return cached[1].model_copy(deep=True)
        if cached:
            if key not in self._inflight:
                self._inflight[key] = asyncio.create_task(self._refresh(criteria, key, queries))
                self._inflight[key].add_done_callback(lambda task, k=key: self._finish_refresh(k, task))
            response = cached[1].model_copy(deep=True)
            response.message = "Showing cached jobs while sources refresh."
            return response
        if key not in self._inflight:
            self._inflight[key] = asyncio.create_task(self._refresh(criteria, key, queries))
            self._inflight[key].add_done_callback(lambda task, k=key: self._finish_refresh(k, task))
        return (await asyncio.shield(self._inflight[key])).model_copy(deep=True)

    def _finish_refresh(self, key: str, task: asyncio.Task) -> None:
        self._inflight.pop(key, None)
        if not task.cancelled() and task.exception():
            logger.warning("Job catalog refresh failed: error_type=%s error=%s", type(task.exception()).__name__, task.exception())

    async def _refresh(
        self, criteria: JobSearchCriteria, key: str, supplementary_queries: tuple[str, ...]
    ) -> JobSearchResponse:
        requests = [(source, criteria) for source in self.sources]
        # Google Jobs currently gives one ten-result page for a broad search,
        # while its advertised next-page token returns no results. Seed a small
        # cross-profession catalog, then add verified profile roles and deduplicate.
        browse_queries = ("Accountant", "Nurse", "Marketing") + supplementary_queries
        if not criteria.query and not criteria.page_token:
            requests.extend(
                (source, criteria.model_copy(update={"query": term}))
                for source in self.sources if isinstance(source, SerpApiJobProvider)
                for term in dict.fromkeys(browse_queries)
            )
        outcomes = await asyncio.gather(
            *(source.search(request_criteria) for source, request_criteria in requests),
            return_exceptions=True,
        )
        jobs, failures = [], []
        next_page_token = None
        authority = {source.name: source.authority for source in self.sources}
        for index, ((source, request_criteria), outcome) in enumerate(zip(requests, outcomes, strict=True)):
            if isinstance(outcome, Exception):
                logger.warning(
                    "Job source failed: source=%s query=%r location=%r error_type=%s http_status=%s error=%s",
                    source.name,
                    request_criteria.query,
                    request_criteria.location,
                    type(outcome).__name__,
                    getattr(getattr(outcome, "response", None), "status_code", None),
                    _safe_error(outcome),
                )
                if index < len(self.sources):
                    failures.append(source.name)
            elif isinstance(outcome, JobProviderResult):
                jobs.extend(outcome.jobs)
                next_page_token = outcome.next_page_token or next_page_token
            else:
                jobs.extend(outcome)
        if self.sources and len(failures) == len(self.sources) and not jobs:
            raise RuntimeError("All configured job providers are unavailable")
        for job in jobs:
            job.posted_at = _utc(job.posted_at)
            job.expires_at = _utc(job.expires_at)
        jobs = self._deduplicate(self._filter(jobs, criteria), authority)
        jobs = [job for job in jobs if job.normalized_status not in {"closed", "expired"}]
        jobs.sort(
            key=lambda job: job.posted_at or datetime.min.replace(tzinfo=UTC),
            reverse=True,
        )
        jobs = self._diversify(jobs)
        jobs = jobs[: criteria.limit]
        for job in jobs:
            self._details[(job.source.casefold(), job.external_id)] = job
        response = JobSearchResponse(
            criteria=criteria,
            jobs=jobs,
            result_count=len(jobs),
            source_failures=failures,
            next_page_token=next_page_token,
            message=(
                "No job providers are configured."
                if not self.sources
                else f"{len(jobs)} jobs found. {len(failures)} source was unavailable."
                if failures
                else None
            ),
        )
        self._cache[key] = (time.monotonic(), response)
        return response.model_copy(deep=True)

    def get_details(self, source: str, external_id: str) -> JobResult | None:
        return self._details.get((source.casefold(), external_id))

    @staticmethod
    def _filter(jobs, criteria):
        query = set(_tokens(criteria.query))
        cutoff = {"24h": 1, "7d": 7, "30d": 30}.get(criteria.date_posted or "")
        result = []
        for job in jobs:
            status_text = " ".join(str(value) for value in (
                getattr(job, "normalized_status", ""),
                getattr(job, "source_status", ""),
            )).casefold()
            if any(word in status_text for word in ("closed", "expired", "removed")):
                job.expired = "expired" in status_text
                job.normalized_status = "expired" if job.expired else "closed"
                continue
            if job.expires_at and job.expires_at < datetime.now(UTC):
                job.expired = True
                job.normalized_status = "expired"
                continue
            # Default freshness window. Explicit source-confirmed active jobs are retained
            # when providers have incomplete or imperfect posting dates.
            if (
                job.posted_at
                and job.posted_at < datetime.now(UTC) - timedelta(days=60)
                and job.normalized_status != "active"
            ):
                continue
            text = " ".join(
                [job.title, job.company, job.location or "", _plain(job.description), *job.skills]
            ).casefold()
            if query and not query.intersection(_tokens(text)):
                continue
            if criteria.location and not _location_matches(criteria.location, job.location):
                continue
            if criteria.country and not _location_matches(criteria.country, " ".join(filter(None, (job.country, job.location)))):
                continue
            if criteria.workplace_type and job.workplace_type != criteria.workplace_type:
                continue
            if (
                criteria.employment_type
                and criteria.employment_type.casefold()
                not in (job.employment_type or "").casefold()
            ):
                continue
            if criteria.experience_level and criteria.experience_level.casefold() not in text:
                continue
            if cutoff and (
                not job.posted_at or job.posted_at < datetime.now(UTC) - timedelta(days=cutoff)
            ):
                continue
            result.append(job)
        return result

    @staticmethod
    def _deduplicate(jobs, authority):
        chosen = {}
        for job in jobs:
            semantic = "|".join(
                _normalize(x) for x in (job.company, job.title, job.location or "remote")
            )
            key = semantic or str(job.apply_url).rstrip("/").casefold()
            current = chosen.get(key)
            if not current or (_completeness(job), authority.get(job.source, 0)) > (
                _completeness(current),
                authority.get(current.source, 0),
            ):
                chosen[key] = job
        return list(chosen.values())

    @staticmethod
    def _diversify(jobs: list[JobResult]) -> list[JobResult]:
        """Interleave providers so one large feed cannot monopolize the first page."""
        buckets: dict[str, list[JobResult]] = {}
        for job in jobs:
            buckets.setdefault(job.source, []).append(job)
        result = []
        while buckets:
            for source in list(buckets):
                result.append(buckets[source].pop(0))
                if not buckets[source]:
                    del buckets[source]
        return result

def _plain(value):
    return unescape(HTML.sub(" ", value or ""))


def _safe_error(error: Exception) -> str:
    message = str(error)
    return re.sub(r"https?://[^\s'\"]+", "[provider URL]", message)


def _tokens(value):
    return [token.casefold() for token in TOKEN.findall(value or "")]


def _normalize(value):
    return "".join(_tokens(value))


def _completeness(job: JobResult) -> int:
    values = (
        job.description,
        job.location,
        job.country,
        job.employment_type,
        job.posted_at,
        job.salary_min,
        job.salary_max,
        job.salary_currency,
    )
    return sum(value is not None and value != "" for value in values)


def _location_matches(requested: str, offered: str | None) -> bool:
    """Match the requested place; a worldwide listing is not a local listing."""
    requested_tokens = set(_tokens(requested)) - {"the"}
    offered_text = (offered or "").casefold()
    if not requested_tokens:
        return True
    if any(marker in offered_text for marker in ("worldwide", "anywhere", "global")):
        return False
    return bool(requested_tokens & set(_tokens(offered_text)))


def _utc(value: datetime | None) -> datetime | None:
    """Normalize mixed provider timestamps before filtering and sorting."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
