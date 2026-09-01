from __future__ import annotations

from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class ProfileIntent(StrEnum):
    GREETING = "greeting"
    GENERAL_CONVERSATION = "general_conversation"
    READ_PROFILE = "read_profile"
    READ_SKILLS = "read_skills"
    READ_EDUCATION = "read_education"
    READ_EXPERIENCE = "read_experience"
    READ_PROJECTS = "read_projects"
    ADD_PROFILE_INFORMATION = "add_profile_information"
    UPDATE_PROFILE_INFORMATION = "update_profile_information"
    ADD_EDUCATION = "add_education"
    UPDATE_EDUCATION = "update_education"
    DELETE_EDUCATION = "delete_education"
    ADD_SKILL = "add_skill"
    DELETE_SKILL = "delete_skill"
    ADD_EXPERIENCE = "add_experience"
    UPDATE_EXPERIENCE = "update_experience"
    DELETE_EXPERIENCE = "delete_experience"
    ADD_PROJECT = "add_project"
    UPDATE_PROJECT = "update_project"
    DELETE_PROJECT = "delete_project"
    PROFILE_COMPLETENESS = "profile_completeness"
    PROFILE_GAPS = "profile_gaps"
    NEXT_BEST_ACTION = "next_best_action"
    IMPROVE_WRITING = "improve_writing"
    GENERAL_PROFILE_QUESTION = "general_profile_question"
    UNKNOWN = "unknown"

class IntentResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    intent: ProfileIntent
    domain: str | None = None
    confidence: float = Field(ge=0, le=1)
    requires_profile_context: bool = False
    requires_clarification: bool = False
    fields: dict[str, Any] = Field(default_factory=dict)
    missing_required_fields: list[str] = Field(default_factory=list)
    ambiguities: list[str] = Field(default_factory=list)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)

class ApprovalRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=128)
    decision: str = Field(pattern="^(approve|reject)$")

class Proposal(BaseModel):
    operation: str
    domain: str
    fields: dict[str, Any]

class AgentResponse(BaseModel):
    type: str
    message: str
    thread_id: str
    proposal: Proposal | None = None
    requires_approval: bool = False
