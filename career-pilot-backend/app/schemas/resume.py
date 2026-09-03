from enum import StrEnum
from typing import Any, Literal

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
    template_id: str = "ats_classic"


class ResumeHeader(BaseModel):
    full_name: str = ""
    professional_title: str | None = None
    email: str = ""
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None


class ResumeExperienceItem(BaseModel):
    company: str
    job_title: str
    location: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    is_current: bool = False
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    visible: bool = True


class ResumeEducationItem(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    grade: str | None = None
    grade_system: str | None = None
    description: str | None = None
    visible: bool = True


class ResumeProjectItem(BaseModel):
    name: str
    role: str | None = None
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)
    project_url: str | None = None
    repository_url: str | None = None
    visible: bool = True


class ResumeSkillGroup(BaseModel):
    category: str
    items: list[str]
    visible: bool = True


class ResumeDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    header: ResumeHeader
    summary: str | None = None
    experience: list[ResumeExperienceItem] = Field(default_factory=list)
    education: list[ResumeEducationItem] = Field(default_factory=list)
    projects: list[ResumeProjectItem] = Field(default_factory=list)
    skill_groups: list[ResumeSkillGroup] = Field(default_factory=list)
    section_order: list[str] = Field(default_factory=list)
    hidden_sections: list[str] = Field(default_factory=list)
    review_flags: list[str] = Field(default_factory=list)


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


class ResumeFactValidation(BaseModel):
    valid: bool
    unsupported_claims: list[str] = Field(default_factory=list)


class ResumeUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: ResumeDraft | None = None
    template_id: str | None = None


class ResumeResponse(ORMResponse):
    title: str
    document_type: Literal["resume", "cv"]
    version: int
    status: ResumeStatus
    template_id: str
    language: str
    content: dict[str, Any]


class ResumeReadiness(BaseModel):
    ready: bool
    career_stage: str
    available: dict[str, int]
    missing: list[str]
    guidance: list[str]


class ResumeSelection(BaseModel):
    section: Literal["summary", "experience", "projects", "education", "skills"]
    item_index: int | None = Field(default=None, ge=0)
    bullet_index: int | None = Field(default=None, ge=0)


class ResumeEvidence(BaseModel):
    source_type: Literal["profile", "career_knowledge", "user_answer"]
    domain: str
    excerpt: str | None = None


class ResumeSuggestion(BaseModel):
    id: str
    section: str
    item_index: int | None = None
    bullet_index: int | None = None
    type: Literal[
        "rewrite", "shorten", "strengthen", "add_existing_fact",
        "remove_generic_content", "ask_for_detail", "missing_metric",
    ]
    suggestion: str | None = None
    label: str
    reason: str
    evidence: list[ResumeEvidence] = Field(default_factory=list)
    requires_confirmation: bool = False
    variants: list[str] = Field(default_factory=list, max_length=3)


class ResumeIssue(BaseModel):
    type: str
    message: str


class ResumeSectionAnalysis(BaseModel):
    section: str
    item_index: int | None = None
    quality: Literal["strong", "good", "needs_improvement", "weak", "insufficient_information"]
    issues: list[ResumeIssue] = Field(default_factory=list)
    strengths: list[str] = Field(default_factory=list)
    supported_suggestions: list[ResumeSuggestion] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
    clarification_questions: list[str] = Field(default_factory=list, max_length=1)


class ResumeAnalysisResponse(BaseModel):
    analyses: list[ResumeSectionAnalysis]
    top_priority: ResumeSectionAnalysis | None = None


class ResumeCoachRequest(BaseModel):
    selection: ResumeSelection
    message: str = Field(default="Analyze this section", max_length=1000)
    user_answer: str | None = Field(default=None, max_length=2000)


class ResumeCoachResponse(BaseModel):
    selection: ResumeSelection
    analysis: ResumeSectionAnalysis
    detected_intent: str
    response_language: Literal["en", "ar"]
    relevant_context: list[str] = Field(default_factory=list)
    profile_update_requires_approval: bool = False


class ResumeSuggestionApply(BaseModel):
    suggestion: ResumeSuggestion
    edited_text: str | None = Field(default=None, max_length=4000)
    confirmed: bool = False
