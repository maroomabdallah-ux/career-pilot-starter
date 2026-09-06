from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import UTC, datetime, timedelta
from html import unescape

from app.integrations.job_sources import ArbeitnowJobSource, JobSourceAdapter, RemotiveJobSource
from app.schemas.job import JobResult, JobSearchCriteria, JobSearchResponse

logger = logging.getLogger(__name__)
TOKEN = re.compile(r"[a-z0-9+#.]{2,}", re.I)
HTML = re.compile(r"<[^>]+>")


class JobSearchService:
    def __init__(self, sources: list[JobSourceAdapter] | None = None, cache_ttl: int = 180):
        self.sources = sources or [RemotiveJobSource(), ArbeitnowJobSource()]
        self.cache_ttl = cache_ttl
        self._cache: dict[str, tuple[float, JobSearchResponse]] = {}
        self._details: dict[tuple[str, str], JobResult] = {}

    async def search(
        self, criteria: JobSearchCriteria, profile_skills: list[str] | None = None
    ) -> JobSearchResponse:
        key = criteria.model_dump_json()
        cached = self._cache.get(key)
        if cached and time.monotonic() - cached[0] < self.cache_ttl:
            return cached[1].model_copy(deep=True)
        outcomes = await asyncio.gather(
            *(source.search(criteria) for source in self.sources), return_exceptions=True
        )
        jobs, failures = [], []
        authority = {source.name: source.authority for source in self.sources}
        for source, outcome in zip(self.sources, outcomes, strict=True):
            if isinstance(outcome, Exception):
                logger.warning(
                    "Job source failed", extra={"job_source": source.name}, exc_info=outcome
                )
                failures.append(source.name)
            else:
                jobs.extend(outcome)
        jobs = self._deduplicate(self._filter(jobs, criteria), authority)
        jobs = [self._score(job, criteria, profile_skills or []) for job in jobs if not job.expired]
        jobs.sort(
            key=lambda job: (
                job.relevance_score or 0,
                job.posted_at or datetime.min.replace(tzinfo=UTC),
            ),
            reverse=True,
        )
        jobs = jobs[: criteria.limit]
        for job in jobs:
            self._details[(job.source.casefold(), job.external_id)] = job
        response = JobSearchResponse(
            criteria=criteria,
            jobs=jobs,
            result_count=len(jobs),
            source_failures=failures,
            message=(
                f"{len(jobs)} jobs found. {len(failures)} source was unavailable."
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
        query = set(_tokens(criteria.query)) | {s.casefold() for s in criteria.skills}
        cutoff = {"24h": 1, "7d": 7, "30d": 30}.get(criteria.date_posted or "")
        result = []
        for job in jobs:
            text = " ".join(
                [job.title, job.company, job.location or "", _plain(job.description), *job.skills]
            ).casefold()
            if query and not query.intersection(_tokens(text)):
                continue
            if (
                criteria.location
                and criteria.location.casefold() not in text
                and job.workplace_type != "remote"
            ):
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
            if job.expires_at and job.expires_at < datetime.now(UTC):
                job.expired = True
            result.append(job)
        return result

    @staticmethod
    def _deduplicate(jobs, authority):
        chosen = {}
        for job in jobs:
            url_key = str(job.apply_url).rstrip("/").casefold()
            semantic = "|".join(
                _normalize(x) for x in (job.company, job.title, job.location or "remote")
            )
            key = url_key if url_key in chosen else semantic
            current = chosen.get(key)
            if not current or authority.get(job.source, 0) > authority.get(current.source, 0):
                chosen[key] = job
        return list(chosen.values())

    @staticmethod
    def _score(job, criteria, profile_skills):
        text = " ".join([job.title, _plain(job.description), *job.skills]).casefold()
        title_tokens = set(_tokens(criteria.query))
        title_overlap = title_tokens.intersection(_tokens(job.title))
        verified = {skill.casefold(): skill for skill in profile_skills}
        matched = [name for key, name in verified.items() if key in text]
        advertised = {skill for skill in job.skills if skill.casefold() not in verified}
        score = min(100, 30 + 8 * len(title_overlap) + 7 * min(len(matched), 4))
        reasons = []
        if title_overlap:
            reasons.append("Job title aligns with your search")
        if matched:
            reasons.append(f"Profile skills matched: {', '.join(matched[:3])}")
        if criteria.workplace_type and job.workplace_type == criteria.workplace_type:
            score = min(100, score + 10)
            reasons.append(f"{job.workplace_type.title()} matches your preference")
        job.relevance_score = score
        job.matched_skills = matched
        job.skill_gaps = sorted(advertised, key=str.casefold)[:5]
        job.fit_reasons = reasons
        return job


def _plain(value):
    return unescape(HTML.sub(" ", value or ""))


def _tokens(value):
    return [token.casefold() for token in TOKEN.findall(value or "")]


def _normalize(value):
    return "".join(_tokens(value))
