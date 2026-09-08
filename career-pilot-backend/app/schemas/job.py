from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, computed_field, field_validator

WorkplaceType = Literal["remote", "hybrid", "on-site", "unknown"]


class JobSearchCriteria(BaseModel):
    query: str = Field(min_length=2, max_length=200)
    location: str | None = Field(default=None, max_length=160)
    country: str | None = Field(default=None, max_length=100)
    workplace_type: WorkplaceType | None = None
    employment_type: str | None = Field(default=None, max_length=60)
    experience_level: str | None = Field(default=None, max_length=60)
    date_posted: Literal["24h", "7d", "30d"] | None = None
    skills: list[str] = Field(default_factory=list, max_length=25)
    limit: int = Field(default=20, ge=1, le=50)
    page_token: str | None = Field(default=None, max_length=2048)

    @field_validator("query", "location", "country", "employment_type", "experience_level")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class JobResult(BaseModel):
    match_score: int | None = Field(default=None, ge=0, le=100)
    external_id: str
    source: str
    source_url: HttpUrl
    title: str
    company: str
    company_logo: HttpUrl | None = None
    via: str | None = None
    apply_options: list[dict[str, str]] = Field(default_factory=list)
    location: str | None = None
    country: str | None = None
    workplace_type: WorkplaceType = "unknown"
    employment_type: str | None = None
    experience_level: str | None = None
    description: str | None = None
    requirements: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str | None = None
    posted_at: datetime | None = None
    expires_at: datetime | None = None
    apply_url: HttpUrl
    retrieved_at: datetime
    relevance_score: int | None = Field(default=None, ge=0, le=100)
    matched_skills: list[str] = Field(default_factory=list)
    skill_gaps: list[str] = Field(default_factory=list)
    fit_reasons: list[str] = Field(default_factory=list)
    expired: bool = False

    @computed_field
    @property
    def id(self) -> str:
        return self.external_id

    @computed_field
    @property
    def salary(self) -> str | None:
        if self.salary_min is None and self.salary_max is None:
            return None
        values = [self.salary_min, self.salary_max]
        amount = " – ".join(f"{value:,.0f}" for value in values if value is not None)
        return f"{amount} {self.salary_currency or ''}".strip()


class JobSearchResponse(BaseModel):
    criteria: JobSearchCriteria
    jobs: list[JobResult]
    result_count: int
    source_failures: list[str] = Field(default_factory=list)
    message: str | None = None
    next_page_token: str | None = None


class PaginatedJobSearchResponse(BaseModel):
    jobs: list[JobResult]
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
    source_failures: list[str] = Field(default_factory=list)
    message: str | None = None
    total_pages: int = 1
    context_sources: list[str] = Field(default_factory=list)
    search_query: str = ""
    search_location: str = ""


class JobSearchRequest(BaseModel):
    prompt: str | None = Field(default=None, max_length=500)
    criteria: JobSearchCriteria | None = None


class SavedJobCreate(BaseModel):
    job: JobResult


class SavedJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    source: str
    external_job_id: str
    title: str
    company: str
    location: str | None
    workplace_type: str
    employment_type: str | None
    apply_url: str
    source_url: str
    snapshot: dict
    saved_at: datetime


class SearchHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    criteria: dict
    result_count: int
    sources: list[str]
    source_failures: list[str]
    created_at: datetime
