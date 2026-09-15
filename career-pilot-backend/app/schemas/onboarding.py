from datetime import date

from pydantic import BaseModel, Field


class CVEducation(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class CVExperience(BaseModel):
    company: str
    job_title: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False


class CVProject(BaseModel):
    name: str
    description: str | None = None


class CVReview(BaseModel):
    full_name: str | None = None
    email: str | None = None
    professional_title: str | None = None
    phone: str | None = None
    city: str | None = None
    country: str | None = None
    linkedin_url: str | None = None
    portfolio_url: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    education: list[CVEducation] = Field(default_factory=list)
    experiences: list[CVExperience] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[CVProject] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    missing_fields: list[str] = Field(default_factory=list)


class CVConfirm(BaseModel):
    review: CVReview
