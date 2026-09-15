import io
import re
from datetime import date, datetime

from fastapi import HTTPException, UploadFile
from sqlalchemy import select

from app.models.career_profile import CareerProfile
from app.models.education import Education
from app.models.experience import Experience
from app.models.project import Project
from app.models.skill import Skill
from app.repositories.career_profile import CareerProfileRepository
from app.schemas.onboarding import CVEducation, CVExperience, CVProject, CVReview

SECTION_NAMES = {
    "professional summary": "summary",
    "summary": "summary",
    "technical skills": "skills",
    "skills": "skills",
    "core competencies": "skills",
    "professional experience": "experience",
    "work experience": "experience",
    "experience": "experience",
    "employment": "experience",
    "selected projects": "projects",
    "projects": "projects",
    "education": "education",
    "courses & development": "certifications",
    "courses and development": "certifications",
    "certifications": "certifications",
    "certificates": "certifications",
    "voluntary work": "voluntary",
    "volunteer experience": "voluntary",
}
EMAIL = re.compile(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"(?:\+?\d[\d ()-]{7,}\d)")
DATE_RANGE = re.compile(
    r"\b((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}|\d{4})\s*[-–—]\s*(present|current|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}|\d{4})\b",
    re.I,
)
URL = re.compile(
    r"(?:https?://)?(?:www\.)?[\w.-]+\.[A-Za-z]{2,}(?:/[\w._~:/?#\[\]@!$&'()*+,;=%-]*)?"
)


async def extract_text(file: UploadFile) -> str:
    payload = await file.read(5_000_001)
    if len(payload) > 5_000_000:
        raise HTTPException(413, "CV must be 5 MB or smaller")
    name = (file.filename or "").casefold()
    if name.endswith(".pdf"):
        try:
            from pypdf import PdfReader

            return "\n".join(
                page.extract_text() or "" for page in PdfReader(io.BytesIO(payload)).pages
            )
        except Exception as exc:
            raise HTTPException(422, "The PDF text could not be read") from exc
    if name.endswith((".txt", ".md")) or (file.content_type or "").startswith("text/"):
        return payload.decode("utf-8", errors="replace")
    raise HTTPException(415, "Upload a text-based PDF or TXT CV")


def parse_cv_text(text: str) -> CVReview:
    lines = [re.sub(r"^[•*\-]\s*", "", x).strip() for x in text.splitlines() if x.strip()]
    sections: dict[str, list[str]] = {}
    current = "header"
    for line in lines:
        heading = _section_name(line)
        if heading:
            current = heading
            sections.setdefault(current, [])
        else:
            sections.setdefault(current, []).append(line)
    header = sections.get("header", [])
    title = next(
        (
            line
            for line in header[1:]
            if not EMAIL.search(line) and not PHONE.search(line) and len(line) <= 160
        ),
        None,
    )
    skills = _parse_skills(sections.get("skills", []))
    education = _parse_education(sections.get("education", []))
    experience = _parse_experience(sections.get("experience", []))
    projects = _parse_projects(sections.get("projects", []))
    certifications = _parse_certifications(sections.get("certifications", []))
    location = next((line for line in header if "amman" in line.casefold()), "")
    city, country = _location(location)
    links = [
        match.group(0).rstrip(".,")
        for match in URL.finditer(text)
        if not match.start() or text[match.start() - 1] != "@"
    ]
    links = [link for link in links if _is_web_link(link)]
    linkedin = next((url for url in links if "linkedin.com" in url.casefold()), None)
    portfolio = next(
        (
            url
            for url in links
            if "linkedin.com" not in url.casefold() and "github.com" not in url.casefold()
        ),
        None,
    )
    result = CVReview(
        full_name=header[0] if header else None,
        email=(EMAIL.search(text).group(0) if EMAIL.search(text) else None),
        professional_title=title,
        phone=(PHONE.search(text).group(0).strip() if PHONE.search(text) else None),
        city=city,
        country=country,
        linkedin_url=_web_url(linkedin),
        portfolio_url=_web_url(portfolio),
        target_roles=[title] if title else [],
        education=education,
        experiences=experience,
        skills=skills,
        projects=projects,
        certifications=certifications,
    )
    result.missing_fields = [
        label
        for label, missing in (
            ("professional_title", not result.professional_title),
            ("target_roles", not result.target_roles),
            ("education", not result.education),
            ("skills", not result.skills),
        )
        if missing
    ]
    return result


def _section_name(line: str) -> str | None:
    normalized = re.sub(r"\s+", " ", line.casefold().strip(" :"))
    return SECTION_NAMES.get(normalized)


def _parse_skills(lines: list[str]) -> list[str]:
    skills = []
    for line in lines:
        value = line.split(":", 1)[-1] if ":" in line else line
        skills.extend(x.strip(" .") for x in re.split(r"[,;|]", value) if x.strip(" ."))
    return list(dict.fromkeys(skills))[:80]


def _parse_education(lines: list[str]) -> list[CVEducation]:
    entries = []
    for line in lines:
        if (
            "bachelor" in line.casefold()
            or "master" in line.casefold()
            or "diploma" in line.casefold()
        ):
            if "|" in line:
                degree, _, institution = line.partition("|")
            elif "—" in line:
                institution, _, degree = line.partition("—")
            else:
                degree, institution = line, "Not specified"
            entries.append(
                CVEducation(
                    degree=degree.strip(),
                    institution=institution.split(",")[0].strip() or "Not specified",
                    field_of_study=_field_of_study(degree),
                    **_date_fields(line),
                )
            )
    return entries[:5]


def _parse_experience(lines: list[str]) -> list[CVExperience]:
    entries, current = [], None
    for line in lines:
        is_dated_role = "|" in line and re.search(r"\b(?:19|20)\d{2}\b", line)
        is_simple_role = bool(re.search(r"\s+(?:at|@)\s+", line, re.I))
        if is_dated_role or is_simple_role:
            if current:
                entries.append(current)
            if is_dated_role:
                parts = [part.strip() for part in line.split("|")]
                employer = parts[1].split(" - ")[0].strip() if len(parts) > 1 else "Not specified"
                current = CVExperience(company=employer, job_title=parts[0], **_date_fields(line))
            else:
                title, employer = re.split(r"\s+(?:at|@)\s+", line, maxsplit=1, flags=re.I)
                current = CVExperience(company=employer, job_title=title)
        elif current:
            current.description = " ".join(filter(None, [current.description, line]))
    if current:
        entries.append(current)
    return entries[:10]


def _parse_projects(lines: list[str]) -> list[CVProject]:
    entries, current = [], None
    for line in lines:
        if "|" in line and not line.casefold().startswith("github:"):
            if current:
                entries.append(current)
            current = CVProject(name=line.split("|", 1)[0].strip())
        elif current:
            current.description = " ".join(filter(None, [current.description, line]))
    if current:
        entries.append(current)
    if not entries:
        entries = [CVProject(name=line) for line in lines if line][:8]
    return entries[:10]


def _parse_certifications(lines: list[str]) -> list[str]:
    return [line.strip(" .") for line in lines if line.strip(" .")][:20]


def _field_of_study(degree: str) -> str | None:
    match = re.search(r"(?:of|in)\s+(.+)$", degree, re.I)
    return match.group(1).strip() if match else None


def _date_fields(value: str) -> dict[str, date | bool | None]:
    """Map explicitly written CV date ranges; never invent dates."""
    match = DATE_RANGE.search(value)
    if not match:
        return {"start_date": None, "end_date": None, "is_current": False}
    start, end = _parse_month_year(match.group(1)), match.group(2).casefold()
    current = end in {"present", "current"}
    return {
        "start_date": start,
        "end_date": None if current else _parse_month_year(match.group(2)),
        "is_current": current,
    }


def _parse_month_year(value: str) -> date | None:
    value = value.strip()
    if re.fullmatch(r"\d{4}", value):
        return date(int(value), 1, 1)
    for pattern in ("%b %Y", "%B %Y"):
        try:
            return datetime.strptime(value.title(), pattern).date().replace(day=1)
        except ValueError:
            continue
    return None


def _location(value: str) -> tuple[str | None, str | None]:
    parts = [part.strip() for part in re.split(r"[,|]", value) if part.strip()]
    return (parts[0], parts[1]) if len(parts) >= 2 else (None, None)


def _web_url(value: str | None) -> str | None:
    if not value:
        return None
    return value if value.startswith(("http://", "https://")) else f"https://{value}"


def _is_web_link(value: str) -> bool:
    return bool(
        re.search(
            r"\.(?:com|net|org|io|dev|me|app|co|ai|site|online|tech|xyz|info)(?:/|$)", value, re.I
        )
    )


async def confirm_cv_review(session, user, review: CVReview):
    # The CV can contain an old or alternate email. Account email changes are
    # intentionally handled in account settings, not as a side effect of CV import.
    if review.full_name:
        names = review.full_name.split(maxsplit=1)
        user.first_name = names[0]
        user.last_name = names[1] if len(names) > 1 else user.last_name
    profile = await CareerProfileRepository(session).get_by_user_id(user.id)
    if not profile:
        profile = CareerProfile(user_id=user.id)
        session.add(profile)
        await session.flush()
    for field in (
        "professional_title",
        "phone",
        "city",
        "country",
        "linkedin_url",
        "portfolio_url",
        "target_roles",
    ):
        value = getattr(review, field)
        if value:
            setattr(profile, field, value)
    session.add_all(
        [Education(career_profile_id=profile.id, **x.model_dump()) for x in review.education]
    )
    session.add_all(
        [Experience(career_profile_id=profile.id, **x.model_dump()) for x in review.experiences]
    )
    session.add_all(
        [Project(career_profile_id=profile.id, **x.model_dump()) for x in review.projects]
    )
    existing = {
        name.casefold()
        for name in await session.scalars(
            select(Skill.name).where(Skill.career_profile_id == profile.id)
        )
    }
    session.add_all(
        [
            Skill(career_profile_id=profile.id, name=x)
            for x in review.skills
            if x.casefold() not in existing
        ]
    )
    await session.commit()
    return await CareerProfileRepository(session).get_by_user_id(user.id)
