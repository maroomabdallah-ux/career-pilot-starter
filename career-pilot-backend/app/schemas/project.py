from datetime import date

from pydantic import ConfigDict, Field, HttpUrl

from app.schemas.common import DateRangeMixin, ORMResponse


class ProjectBase(DateRangeMixin):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    role: str | None = None
    technologies: list[str] = Field(default_factory=list)
    project_url: HttpUrl | None = None
    repository_url: HttpUrl | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(DateRangeMixin):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    role: str | None = None
    technologies: list[str] | None = None
    project_url: HttpUrl | None = None
    repository_url: HttpUrl | None = None
    start_date: date | None = None
    end_date: date | None = None


class ProjectResponse(ProjectBase, ORMResponse):
    pass
