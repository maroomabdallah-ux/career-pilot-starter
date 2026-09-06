from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from app.mcp.clients.core_client import CareerPilotMCPClient
from app.models.user import User

logger = logging.getLogger(__name__)


def evaluate_resume_readiness(profile) -> dict[str, Any]:
    if isinstance(profile, dict):
        education = profile.get("education", [])
        experiences = profile.get("experience", [])
        projects = profile.get("projects", [])
        skills = profile.get("skills", [])
    else:
        education = profile.education
        experiences = profile.experiences
        projects = profile.projects
        skills = profile.skills
    available = {
        "education": len(education),
        "experience": len(experiences),
        "projects": len(projects),
        "skills": len(skills),
    }
    stage = "experienced" if experiences else ("student" if education else "early_career")
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

    def __init__(self, user: User, access_token: str, client: CareerPilotMCPClient | None = None):
        self.user = user
        self.client = client or CareerPilotMCPClient(access_token)

    async def build(self, include_projects: bool = True, with_rag: bool = True) -> ResumeContext:
        async with self.client.read_session() as mcp:
            profile = await mcp.get_profile()
            skills = await mcp.get_skills()
            experiences = await mcp.get_experience()
            education = await mcp.get_education()
            projects = await mcp.get_projects() if include_projects else []

            source = {
                "education": education,
                "experience": experiences,
                "projects": projects,
                "skills": skills,
            }
            readiness = evaluate_resume_readiness(source)
            rag = await self._supporting_rag(mcp, experiences, projects) if with_rag else []

        order = (
            ["summary", "experience", "skills", "projects", "education"]
            if readiness["career_stage"] == "experienced"
            else ["summary", "education", "projects", "skills", "experience"]
        )
        verified = {
            "header": {
                "full_name": f"{self.user.first_name} {self.user.last_name}".strip(),
                "email": self.user.email,
                "professional_title": profile.get("professional_title"),
                "location": ", ".join(filter(None, [profile.get("city"), profile.get("country")]))
                or None,
                "phone": profile.get("phone"),
                "linkedin": profile.get("linkedin_url"),
                "github": profile.get("github_url"),
                "portfolio": profile.get("portfolio_url"),
            },
            "summary": profile.get("professional_summary"),
            "experience": [
                {
                    "company": x["company"],
                    "job_title": x["job_title"],
                    "location": x.get("location"),
                    "start_date": x.get("start_date"),
                    "end_date": x.get("end_date"),
                    "is_current": x.get("is_current", False),
                    "bullets": ([x["description"]] if x.get("description") else [])
                    + list(x.get("achievements") or []),
                    "technologies": list(x.get("technologies") or []),
                    "visible": True,
                }
                for x in experiences
            ],
            "education": [
                {
                    "institution": x["institution"],
                    "degree": x.get("degree"),
                    "field_of_study": x.get("field_of_study"),
                    "start_date": x.get("start_date"),
                    "end_date": x.get("end_date"),
                    "grade": x.get("grade"),
                    "grade_system": x.get("grade_system"),
                    "description": x.get("description"),
                    "visible": True,
                }
                for x in education
            ],
            "projects": [
                {
                    "name": x["name"],
                    "role": x.get("role"),
                    "description": x.get("description"),
                    "technologies": list(x.get("technologies") or []),
                    "project_url": x.get("project_url"),
                    "repository_url": x.get("repository_url"),
                    "start_date": x.get("start_date"),
                    "end_date": x.get("end_date"),
                    "is_current": x.get("is_current", False),
                    "visible": True,
                }
                for x in projects
            ]
            if include_projects
            else [],
            "skills": [{"name": x["name"], "category": x.get("category")} for x in skills],
            "section_order": order,
            "hidden_sections": [],
            "review_flags": [],
        }
        return ResumeContext(verified=verified, supporting_rag=rag[:6], readiness=readiness)

    async def _supporting_rag(self, mcp, experiences, projects) -> list[str]:
        searches = [
            {
                "query": "professional career summary responsibilities achievements",
                "domain": "career",
                "limit": 2,
            }
        ]
        searches.extend(
            {
                "query": f"{item['company']} {item['job_title']}",
                "domain": "career",
                "company": item["company"],
                "limit": 2,
            }
            for item in experiences[:2]
        )
        searches.extend(
            {
                "query": item["name"],
                "domain": "career",
                "project": item["name"],
                "limit": 2,
            }
            for item in projects[:2]
        )
        rag: list[str] = []
        try:
            for search in searches:
                chunks = await mcp.search_career_knowledge(**search)
                rag.extend(
                    chunk["content"]
                    for chunk in chunks
                    if chunk.get("content") and chunk["content"] not in rag
                )
        except Exception:
            logger.warning(
                "Optional MCP RAG retrieval failed; continuing with verified profile",
                extra={"user_id": str(self.user.id)},
                exc_info=True,
            )
        return rag[:6]
