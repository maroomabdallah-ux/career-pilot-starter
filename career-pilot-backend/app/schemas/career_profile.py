from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.schemas.common import ORMResponse
from app.schemas.education import EducationResponse
from app.schemas.experience import ExperienceResponse
from app.schemas.project import ProjectResponse
from app.schemas.skill import SkillResponse


class CareerProfileBase(BaseModel):
    professional_title: str | None = None
    professional_summary: str | None = None
    profile_picture: str | None = Field(default=None, max_length=1_500_000)
    phone: str | None = None
    city: str | None = None
    country: str | None = None
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None
    target_roles: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    preferred_work_modes: list[str] = Field(default_factory=list)
    years_of_experience: float = Field(default=0, ge=0)

    @field_validator("profile_picture")
    @classmethod
    def validate_profile_picture(cls, value: str | None):
        if value and not value.startswith(
            ("data:image/jpeg;base64,", "data:image/png;base64,", "data:image/webp;base64,")
        ):
            raise ValueError("profile_picture must be a JPEG, PNG, or WebP image")
        return value


class CareerProfileCreate(CareerProfileBase):
    user_id: UUID


class CareerProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    professional_title: str | None = None
    professional_summary: str | None = None
    profile_picture: str | None = Field(default=None, max_length=1_500_000)
    phone: str | None = None
    city: str | None = None
    country: str | None = None
    linkedin_url: HttpUrl | None = None
    github_url: HttpUrl | None = None
    portfolio_url: HttpUrl | None = None
    target_roles: list[str] | None = None
    preferred_locations: list[str] | None = None
    preferred_work_modes: list[str] | None = None
    years_of_experience: float | None = Field(default=None, ge=0)

    @field_validator("profile_picture")
    @classmethod
    def validate_profile_picture(cls, value: str | None):
        if value and not value.startswith(
            ("data:image/jpeg;base64,", "data:image/png;base64,", "data:image/webp;base64,")
        ):
            raise ValueError("profile_picture must be a JPEG, PNG, or WebP image")
        return value


class CareerProfileResponse(CareerProfileBase, ORMResponse):
    user_id: UUID
    education: list[EducationResponse] = Field(default_factory=list)
    experiences: list[ExperienceResponse] = Field(default_factory=list)
    projects: list[ProjectResponse] = Field(default_factory=list)
    skills: list[SkillResponse] = Field(default_factory=list)
