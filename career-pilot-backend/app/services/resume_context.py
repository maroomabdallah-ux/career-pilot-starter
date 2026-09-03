from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.services.career_knowledge import CareerKnowledgeConfigurationError, CareerKnowledgeService
from app.services.me import MeService

logger = logging.getLogger(__name__)


def _date(value):
    return value.isoformat() if value else None


def evaluate_resume_readiness(profile) -> dict[str, Any]:
    available = {
        "education": len(profile.education),
        "experience": len(profile.experiences),
        "projects": len(profile.projects),
        "skills": len(profile.skills),
    }
    stage = (
        "experienced"
        if profile.experiences
        else ("student" if profile.education else "early_career")
    )
    ready = bool(
        available["skills"]
        and (available["experience"] or available["projects"] or available["education"])
    )
    missing = [name for name, count in available.items() if not count]
    guidance = [f"Add {name} to strengthen your resume." for name in missing]
    if not ready:
        guidance.insert(0, "Add skills and at least one experience, project, or education entry.")
    return {
        "ready": ready,
        "career_stage": stage,
        "available": available,
        "missing": missing,
        "guidance": guidance,
    }


@dataclass
class ResumeContext:
    verified: dict[str, Any]
    supporting_rag: list[str]
    readiness: dict[str, Any]


class ResumeContextBuilder:
    """Builds server-trusted resume context. Structured profile always wins over RAG."""

    def __init__(self, session: AsyncSession, user: User):
        self.session, self.user = session, user

    async def build(self, include_projects: bool = True, with_rag: bool = True) -> ResumeContext:
        profile = await MeService(self.session, self.user).profile()
        readiness = evaluate_resume_readiness(profile)
        order = (
            ["summary", "experience", "skills", "projects", "education"]
            if readiness["career_stage"] == "experienced"
            else ["summary", "education", "projects", "skills", "experience"]
        )
        verified = {
            "header": {
                "full_name": f"{self.user.first_name} {self.user.last_name}".strip(),
                "email": self.user.email,
                "professional_title": profile.professional_title,
                "location": ", ".join(filter(None, [profile.city, profile.country])) or None,
                "phone": profile.phone,
                "linkedin": profile.linkedin_url,
                "github": profile.github_url,
                "portfolio": profile.portfolio_url,
            },
            "summary": profile.professional_summary,
            "experience": [
                {
                    "company": x.company,
                    "job_title": x.job_title,
                    "location": x.location,
                    "start_date": _date(x.start_date),
                    "end_date": _date(x.end_date),
                    "is_current": x.is_current,
                    "bullets": ([x.description] if x.description else [])
                    + list(x.achievements or []),
                    "technologies": list(x.technologies or []),
                    "visible": True,
                }
                for x in profile.experiences
            ],
            "education": [
                {
                    "institution": x.institution,
                    "degree": x.degree,
                    "field_of_study": x.field_of_study,
                    "start_date": _date(x.start_date),
                    "end_date": _date(x.end_date),
                    "grade": x.grade,
                    "grade_system": x.grade_system,
                    "description": x.description,
                    "visible": True,
                }
                for x in profile.education
            ],
            "projects": [
                {
                    "name": x.name,
                    "role": x.role,
                    "description": x.description,
                    "technologies": list(x.technologies or []),
                    "project_url": x.project_url,
                    "repository_url": x.repository_url,
                    "visible": True,
                }
                for x in profile.projects
            ]
            if include_projects
            else [],
            "skills": [{"name": x.name, "category": x.category} for x in profile.skills],
            "section_order": order,
            "hidden_sections": [],
            "review_flags": [],
        }
        rag: list[str] = []
        if with_rag:
            queries = ["professional career summary responsibilities achievements"]
            queries += [f"{x.company} {x.job_title}" for x in profile.experiences[:2]]
            queries += [x.name for x in profile.projects[:2]]
            try:
                for query in queries:
                    chunks = await CareerKnowledgeService(self.session, self.user.id).retrieve(
                        query, domain="career", limit=2
                    )
                    rag.extend(chunk.content for chunk in chunks if chunk.content not in rag)
            except CareerKnowledgeConfigurationError:
                logger.info("Resume RAG skipped because embeddings are not configured")
            except Exception:
                logger.warning(
                    "Optional Resume RAG retrieval failed; continuing with verified profile",
                    extra={"user_id": str(self.user.id)},
                    exc_info=True,
                )
        return ResumeContext(verified=verified, supporting_rag=rag[:6], readiness=readiness)
