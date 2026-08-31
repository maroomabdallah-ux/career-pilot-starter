from datetime import date

from pydantic import ConfigDict, Field

from app.schemas.common import DateRangeMixin, ORMResponse


class EducationBase(DateRangeMixin):
    institution: str = Field(min_length=1, max_length=200)
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    grade: str | None = None
    grade_system: str | None = Field(default=None, max_length=50)
    description: str | None = None


class EducationCreate(EducationBase):
    pass


class EducationUpdate(DateRangeMixin):
    model_config = ConfigDict(extra="forbid")
    institution: str | None = Field(default=None, min_length=1)
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool | None = None
    grade: str | None = None
    grade_system: str | None = Field(default=None, max_length=50)
    description: str | None = None


class EducationResponse(EducationBase, ORMResponse):
    pass
