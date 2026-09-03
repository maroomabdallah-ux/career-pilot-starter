from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MCPModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProfileOutput(MCPModel):
    professional_title: str | None = None
    professional_summary: str | None = None
    phone: str | None = None
    city: str | None = None
    country: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    portfolio_url: str | None = None
    target_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_work_modes: list[str] = Field(default_factory=list)
    years_of_experience: float = 0


class SkillOutput(MCPModel):
    id: UUID
    name: str
    category: str | None = None
    proficiency_level: str | None = None
    years_of_experience: float = 0


class ExperienceOutput(MCPModel):
    id: UUID
    company: str
    job_title: str
    employment_type: str | None = None
    location: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    description: str | None = None
    achievements: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)


class EducationOutput(MCPModel):
    id: UUID
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_current: bool = False
    grade: str | None = None
    grade_system: str | None = None
    description: str | None = None


class ProjectOutput(MCPModel):
    id: UUID
    name: str
    description: str | None = None
    role: str | None = None
    technologies: list[str] = Field(default_factory=list)
    project_url: str | None = None
    repository_url: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class CareerKnowledgeOutput(MCPModel):
    content: str
    domain: str | None = None
    company: str | None = None
    project: str | None = None
    source_type: str | None = None
    document_title: str | None = None


class ResumeSummaryOutput(MCPModel):
    id: UUID
    title: str
    document_type: str
    version: int
    status: str
    template_id: str
    language: str
    updated_at: datetime


class ResumeOutput(ResumeSummaryOutput):
    content: dict[str, Any]


def json_output(value: BaseModel | list[BaseModel]) -> dict | list[dict]:
    if isinstance(value, list):
        return [item.model_dump(mode="json") for item in value]
    return value.model_dump(mode="json")
