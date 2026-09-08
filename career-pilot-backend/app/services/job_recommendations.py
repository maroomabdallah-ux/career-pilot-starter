"""User-scoped, deterministic recommendations; no external AI requests."""

import re
from dataclasses import dataclass, field

from sqlalchemy import select

from app.integrations.job_sources.parsing import extract_skills, infer_experience_level
from app.models.resume import Resume
from app.repositories.career_profile import CareerProfileRepository


def words(value):
    return set(re.findall(r"[a-z][a-z0-9+#]*", (value or "").casefold()))


def text_values(value):
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(text_values(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(text_values(v) for v in value)
    return ""


@dataclass
class CareerContext:
    roles: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    location: str = ""
    modes: list[str] = field(default_factory=list)
    text: str = ""
    level: str | None = None
    sources: list[str] = field(default_factory=list)


async def load_career_context(session, user_id):
    profile = await CareerProfileRepository(session).get_by_user_id(user_id)
    resume = await session.scalar(
        select(Resume)
        .where(
            Resume.user_id == user_id, Resume.document_type == "resume", Resume.status != "archived"
        )
        .order_by(Resume.updated_at.desc())
        .limit(1)
    )
    context = CareerContext()
    resume_text = text_values(resume.content) if resume else ""
    if resume:
        context.sources.append("Resume")
    if profile:
        context.sources.append("Career profile")
        context.roles = profile.target_roles or (
            [profile.professional_title] if profile.professional_title else []
        )
        context.location = (profile.preferred_locations or [""])[0] or ", ".join(
            x for x in (profile.city, profile.country) if x
        )
        context.modes = profile.preferred_work_modes or []
        experience = " ".join(
            f"{x.job_title} {x.description or ''} {' '.join(x.technologies or [])}"
            for x in profile.experiences
        )
        projects = " ".join(
            f"{x.name} {x.description or ''} {' '.join(x.technologies or [])}"
            for x in profile.projects
        )
        education = " ".join(
            f"{x.degree or ''} {x.field_of_study or ''}" for x in profile.education
        )
        context.text = f"{profile.professional_summary or ''} {experience} {projects} {education} {resume_text}"
        context.skills = [x.name for x in profile.skills]
        context.level = infer_experience_level(" ".join(context.roles))
        if not context.level and profile.years_of_experience:
            context.level = "senior" if profile.years_of_experience >= 5 else "junior"
    else:
        context.text = resume_text
    if resume:
        header = resume.content.get("header") or {}
        if not context.roles and header.get("professional_title"):
            context.roles = [header["professional_title"]]
        context.location = context.location or header.get("location") or ""
        context.skills += [
            str(skill)
            for group in resume.content.get("skill_groups", [])
            for skill in group.get("items", [])
            if group.get("visible", True)
        ]
    context.skills = sorted(set(context.skills + extract_skills(context.text)))
    return context


def rank_jobs(jobs, context):
    """Weighted evidence coverage, normalized only over available user factors."""
    for job in jobs:
        job.match_score = None
        job.matched_skills, job.skill_gaps, job.fit_reasons = [], [], []
        factors = []
        description = job.description or ""
        advertised = extract_skills(description)
        advertised += [
            skill
            for skill in context.skills
            if skill not in advertised
            and re.search(rf"(?<!\w){re.escape(skill)}(?!\w)", description, re.I)
        ]
        user_skills = {x.casefold() for x in context.skills}
        job.matched_skills = [x for x in advertised if x.casefold() in user_skills]
        job.skill_gaps = [x for x in advertised if x.casefold() not in user_skills]
        if context.skills and advertised:
            factors.append((40, len(job.matched_skills) / max(1, len(advertised))))
            if job.matched_skills:
                job.fit_reasons.append("Shared skills: " + ", ".join(job.matched_skills[:5]))
        if context.roles:
            similarity = max(
                len(words(role) & words(job.title)) / max(1, len(words(role)))
                for role in context.roles
            )
            factors.append((25, similarity))
            if similarity >= 0.5:
                job.fit_reasons.append("Job title aligns with your preferred roles.")
        if context.location and job.location:
            overlap = len(words(context.location) & words(job.location))
            match = overlap / max(1, len(words(context.location)))
            factors.append((15, match))
            if match:
                job.fit_reasons.append("Location overlaps your saved location preference.")
        if context.modes and job.workplace_type != "unknown":
            match = job.workplace_type in context.modes
            factors.append((10, float(match)))
            if match:
                job.fit_reasons.append("Work arrangement matches your preference.")
        if context.level and job.experience_level:
            match = context.level == job.experience_level
            factors.append((5, float(match)))
            if match:
                job.fit_reasons.append("Advertised seniority aligns with your career level.")
        keywords = words(context.text) - {"the", "and", "with", "for", "from", "this"}
        if len(keywords) >= 5 and description:
            factors.append((5, len(keywords & words(description)) / len(keywords)))
        # A location alone is not enough evidence for a meaningful career match.
        if factors and (context.skills or context.roles or len(keywords) >= 5):
            job.match_score = round(
                sum(w * v for w, v in factors) / sum(w for w, _ in factors) * 100
            )
        else:
            job.skill_gaps = []
    return sorted(jobs, key=lambda job: job.match_score or 0, reverse=True)
