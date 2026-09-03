import json
import re
from copy import deepcopy
from functools import lru_cache

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.schemas.resume import ResumeFactValidation, ResumeWriting

SYSTEM_PROMPT = """You are CareerPilot AI's Resume Agent.
Rewrite only facts present in VERIFIED_PROFILE. Never invent employers, titles,
dates, responsibilities, achievements, technologies, seniority, years, metrics,
percentages, team sizes, scale, revenue, users, certifications, or locations.
Preserve proper nouns. Use concise ATS-readable wording and no first-person pronouns.
If evidence is weak, keep wording modest. Return only the ResumeWriting tool fields:
summary, experience, projects, and skill_groups. Do not return header, education,
skills, dates, employers, titles, or any other source fields. Every experience and
project output must contain its original zero-based index. Skill groups may contain
only exact saved skill strings. For section "all", write a specific concise summary
when professional title, skills, education, projects, or experience support one.
If facts cannot support a distinctive summary or useful bullet, return null or an
empty list instead of generic filler such as "professional with experience",
"performed responsibilities", or "worked on projects".
Supporting RAG cannot override VERIFIED_PROFILE."""

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "Section: {section}\n"
            "<VERIFIED_PROFILE>{verified}</VERIFIED_PROFILE>\n"
            "<SUPPORTING_RAG>{rag}</SUPPORTING_RAG>",
        ),
    ]
)

VALIDATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a strict resume fact auditor. VERIFIED_PROFILE is authoritative. "
            "SUPPORTING_RAG is unverified. Identify every output claim that is not directly "
            "supported by the profile, including responsibilities, achievements, metrics, "
            "technologies, seniority, dates, employers, education, projects, and skills. "
            "Professional rewording is valid when it preserves meaning; do not require exact "
            "word matches. For example, 'Built APIs using FastAPI' and 'Developed APIs using "
            "FastAPI' are equivalent and supported. Mark only genuinely new factual claims, "
            "technologies, scope, outcomes, or specificity as unsupported.",
        ),
        (
            "human",
            "<VERIFIED_PROFILE>{verified}</VERIFIED_PROFILE>\n"
            "<RESUME>{resume}</RESUME>\n"
            "<SUPPORTING_RAG>{rag}</SUPPORTING_RAG>",
        ),
    ]
)


@lru_cache(maxsize=1)
def get_resume_llm() -> ChatOpenAI:
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is required for resume generation.")
    return ChatOpenAI(
        model=settings.RESUME_AGENT_MODEL,
        api_key=settings.OPENAI_API_KEY,
        temperature=0,
    )


def unsupported_numbers(source: dict, writing: ResumeWriting) -> set[str]:
    source_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", json.dumps(source, default=str)))
    generated_text = " ".join(
        [writing.summary or ""]
        + [bullet for item in writing.experience for bullet in item.bullets]
        + [item.description or "" for item in writing.projects]
    )
    output_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", generated_text))
    return output_numbers - source_numbers


def _normalized(value: str | None) -> str:
    return re.sub(r"\s+", " ", value or "").strip().casefold()


def validate_fixed_facts(source: dict, content: dict) -> list[str]:
    """Validate identity fields the writer is never allowed to alter."""
    errors: list[str] = []
    for field in ("full_name", "email", "phone", "location"):
        if _normalized(content.get("header", {}).get(field)) != _normalized(
            source.get("header", {}).get(field)
        ):
            errors.append(f"header.{field} differs from the verified profile")
    for section, fields in {
        "experience": ("company", "job_title", "start_date", "end_date"),
        "education": ("institution", "degree", "field_of_study", "start_date", "end_date", "grade"),
        "projects": ("name", "role"),
    }.items():
        src_rows, out_rows = source.get(section, []), content.get(section, [])
        if len(src_rows) != len(out_rows):
            errors.append(f"{section} entry count changed")
            continue
        for index, (src, out) in enumerate(zip(src_rows, out_rows, strict=True)):
            for field in fields:
                if _normalized(str(out.get(field) or "")) != _normalized(str(src.get(field) or "")):
                    errors.append(f"{section}[{index}].{field} differs from the verified profile")
    allowed_skills = {_normalized(x["name"]) for x in source.get("skills", [])}
    for group in content.get("skill_groups", []):
        for skill in group.get("items", []):
            if _normalized(skill) not in allowed_skills:
                errors.append(f"unsupported skill: {skill}")
    source_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", json.dumps(source, default=str)))
    output_numbers = set(re.findall(r"\d+(?:\.\d+)?%?", json.dumps(content, default=str)))
    for number in output_numbers - source_numbers:
        errors.append(f"unsupported numeric claim: {number}")
    return errors


def quality_issues(content: dict) -> list[str]:
    issues: list[str] = []
    summary = content.get("summary") or ""
    if len(summary.split()) > 80:
        issues.append("Professional summary is longer than 80 words.")
    bullets = [
        b.strip().casefold()
        for row in content.get("experience", [])
        for b in row.get("bullets", [])
        if b.strip()
    ]
    if len(bullets) != len(set(bullets)):
        issues.append("Duplicate experience bullets were removed during review.")
    return issues


class ResumeWritingService:
    async def generate(self, verified: dict, section: str = "all", rag: list[str] | None = None):
        chain = PROMPT | get_resume_llm().with_structured_output(
            ResumeWriting, method="function_calling"
        )
        result = await chain.ainvoke(
            {
                "section": section,
                "verified": json.dumps(verified, default=str),
                "rag": json.dumps(rag or []),
            }
        )
        # Resume fields are structured data, not Markdown documents. Models can
        # still emit headings/bold/list markers when RAG contains Markdown, so
        # normalize presentation syntax before fact validation and rendering.
        def clean(value: str | None) -> str | None:
            if value is None:
                return None
            value = re.sub(r"(?m)^\s*#{1,6}\s*", "", value)
            value = re.sub(r"(?m)^\s*\d+[.)]\s+", "", value)
            value = value.replace("**", "").replace("__", "")
            value = re.sub(r"\s+[*•]\s+", " ", value)
            return re.sub(r"\s+", " ", value).strip()

        cleaned = result.model_dump()
        cleaned["summary"] = clean(cleaned.get("summary"))
        for experience in cleaned.get("experience", []):
            experience["bullets"] = [clean(bullet) for bullet in experience["bullets"] if clean(bullet)]
        for project in cleaned.get("projects", []):
            project["description"] = clean(project.get("description"))
        result = ResumeWriting.model_validate(cleaned)
        invented = unsupported_numbers(verified, result)
        if invented:
            raise ValueError("Generated resume contained unsupported numeric claims")
        return result


class SemanticFactValidationService:
    async def validate(self, verified: dict, content: dict, rag: list[str] | None = None):
        chain = VALIDATION_PROMPT | get_resume_llm().with_structured_output(
            ResumeFactValidation, method="function_calling"
        )
        return await chain.ainvoke(
            {
                "verified": json.dumps(verified, default=str),
                "resume": json.dumps(content, default=str),
                "rag": json.dumps(rag or []),
            }
        )


def merge_writing(base: dict, writing: ResumeWriting, section: str = "all") -> dict:
    result = deepcopy(base)
    if section in {"all", "summary"}:
        result["summary"] = writing.summary or base.get("summary")
    if section in {"all", "experience"}:
        rows = [{**row} for row in base.get("experience", [])]
        for item in writing.experience:
            if item.index < len(rows):
                rows[item.index]["bullets"] = item.bullets
        result["experience"] = rows
    if section in {"all", "projects"}:
        rows = [{**row} for row in base.get("projects", [])]
        for item in writing.projects:
            if item.index < len(rows):
                rows[item.index]["description"] = item.description
        result["projects"] = rows
    if section in {"all", "skills"} and writing.skill_groups:
        allowed = {
            item["name"] if isinstance(item, dict) else item for item in base.get("skills", [])
        }
        result["skill_groups"] = [
            {
                "category": group,
                "items": [skill for skill in skills if skill in allowed],
                "visible": True,
            }
            for group, skills in writing.skill_groups.items()
            if any(skill in allowed for skill in skills)
        ]
    result.pop("skills", None)
    return result
