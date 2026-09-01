import json
import re

from langchain_core.prompts import ChatPromptTemplate

from app.agents.profile.service import get_profile_llm
from app.schemas.resume import ResumeWriting

SYSTEM_PROMPT = """You are CareerPilot AI's Resume Agent. Rewrite only facts present in VERIFIED_PROFILE.
Never invent employers, titles, dates, responsibilities, achievements, technologies, seniority, years,
metrics, percentages, team sizes, scale, revenue, users, certifications, or locations. Preserve proper nouns.
Use concise ATS-readable wording and no first-person pronouns. If evidence is weak, keep wording modest.
Return JSON only. Experience and project indexes must match the supplied arrays. Skill groups may contain
only exact saved skill strings. Supporting RAG is unverified and cannot override VERIFIED_PROFILE."""

PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "Section: {section}\n<VERIFIED_PROFILE>{verified}</VERIFIED_PROFILE>\n<SUPPORTING_RAG>{rag}</SUPPORTING_RAG>",
        ),
    ]
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


class ResumeWritingService:
    async def generate(self, verified: dict, section: str = "all", rag: list[str] | None = None):
        chain = PROMPT | get_profile_llm().with_structured_output(ResumeWriting, method="json_mode")
        result = await chain.ainvoke(
            {
                "section": section,
                "verified": json.dumps(verified, default=str),
                "rag": json.dumps(rag or []),
            }
        )
        invented = unsupported_numbers(verified, result)
        if invented:
            raise ValueError("Generated resume contained unsupported numeric claims")
        return result


def merge_writing(base: dict, writing: ResumeWriting, section: str = "all") -> dict:
    result = {**base}
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
        allowed = set(base.get("skills", []))
        result["skill_groups"] = {
            group: [skill for skill in skills if skill in allowed]
            for group, skills in writing.skill_groups.items()
        }
    return result
