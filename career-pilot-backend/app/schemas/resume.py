from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMResponse


class ResumeStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ARCHIVED = "archived"


class ResumeGenerate(BaseModel):
    title: str = Field(default="Master Resume", min_length=1, max_length=200)
    language: str = Field(default="en", pattern="^(en|ar)$")
    include_projects: bool = True


class ResumeSection(StrEnum):
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    PROJECTS = "projects"
    SKILLS = "skills"


class ResumeRegenerate(BaseModel):
    section: ResumeSection


class ExperienceWriting(BaseModel):
    index: int = Field(ge=0)
    bullets: list[str] = Field(default_factory=list, max_length=6)


class ProjectWriting(BaseModel):
    index: int = Field(ge=0)
    description: str | None = None


class ResumeWriting(BaseModel):
    model_config = ConfigDict(extra="forbid")
    summary: str | None = None
    experience: list[ExperienceWriting] = Field(default_factory=list)
    projects: list[ProjectWriting] = Field(default_factory=list)
    skill_groups: dict[str, list[str]] = Field(default_factory=dict)


class ResumeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: dict[str, Any] | None = None


class ResumeResponse(ORMResponse):
    title: str
    resume_type: str
    status: ResumeStatus
    language: str
    content: dict[str, Any]
