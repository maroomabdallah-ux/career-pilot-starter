from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ORMResponse


class SkillBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str | None = None
    proficiency_level: str | None = None
    years_of_experience: float = Field(default=0, ge=0)


class SkillCreate(SkillBase):
    pass


class SkillUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=1)
    category: str | None = None
    proficiency_level: str | None = None
    years_of_experience: float | None = Field(default=None, ge=0)


class SkillResponse(SkillBase, ORMResponse):
    pass
