from datetime import date

from pydantic import ConfigDict, Field

from app.schemas.common import DateRangeMixin, ORMResponse


class ExperienceBase(DateRangeMixin):
    company: str = Field(min_length=1, max_length=200)
    job_title: str = Field(min_length=1, max_length=200)
    employment_type: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str | None = None
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceUpdate(DateRangeMixin):
    model_config = ConfigDict(extra="forbid")
    company: str | None = Field(default=None, min_length=1)
    job_title: str | None = Field(default=None, min_length=1)
    employment_type: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    description: str | None = None
    achievements: list[str] | None = None
    technologies: list[str] | None = None


class ExperienceResponse(ExperienceBase, ORMResponse):
    pass
