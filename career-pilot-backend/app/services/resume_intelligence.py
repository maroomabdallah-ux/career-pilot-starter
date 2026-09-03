from __future__ import annotations

import re
from copy import deepcopy
from uuid import uuid4

from app.schemas.resume import (
    ResumeAnalysisResponse, ResumeEvidence, ResumeIssue, ResumeSectionAnalysis,
    ResumeSelection, ResumeSuggestion,
)

GENERIC = re.compile(
    r"^(performed responsibilities|worked on projects?|helped the team|responsible for (development|responsibilities)|worked at .+|performed responsibilities at .+ in role .+)[.!]?$",
    re.I,
)
WEAK_VALUES = {"", "n/a", "na", "none", "f", "test", "-"}


def _words(value: str | None) -> list[str]:
    return re.findall(r"[\w+#.-]+", value or "", re.UNICODE)


def _substantive(value: str | None) -> bool:
    text = (value or "").strip()
    return text.casefold() not in WEAK_VALUES and len(_words(text)) >= 4 and not GENERIC.match(text)


def _question(section: str, item: dict, language: str = "en") -> str:
    ar = language == "ar"
    if section == "experience":
        company = item.get("company") or "this company"
        return f"ما الذي عملت عليه بشكل أساسي في {company}؟" if ar else f"What did you mainly work on at {company}?"
    if section == "projects":
        return "ما المشكلة التي يحلها هذا المشروع؟" if ar else "What problem does this project solve?"
    if section == "summary":
        return "ما نوع الدور الذي تستهدفه؟" if ar else "What type of role are you targeting?"
    if section == "education":
        return "هل لديك تميّز أكاديمي موثق تود إضافته؟" if ar else "Do you have a verified academic distinction you would like to include?"
    return "هل توجد مهارات أخرى موثقة في ملفك تريد تضمينها؟" if ar else "Which verified profile skills are most relevant to your target role?"


def _rag_terms(rag: list[str], item: dict) -> list[str]:
    anchors = [str(item.get(k, "")).casefold() for k in ("company", "job_title", "name")]
    relevant = [x.strip() for x in rag if any(a and a in x.casefold() for a in anchors)]
    return relevant[:3]


def _suggestion(section: str, item_index: int | None, kind: str, label: str, reason: str,
                text: str | None = None, evidence: list[ResumeEvidence] | None = None,
                confirmation: bool = False) -> ResumeSuggestion:
    return ResumeSuggestion(id=str(uuid4()), section=section, item_index=item_index, type=kind,
        label=label, reason=reason, suggestion=text, evidence=evidence or [],
        requires_confirmation=confirmation)


def analyze_section(content: dict, verified: dict, section: str, item_index: int | None = None,
                    rag: list[str] | None = None, language: str = "en") -> ResumeSectionAnalysis:
    rag = rag or []
    issues: list[ResumeIssue] = []
    strengths: list[str] = []
    suggestions: list[ResumeSuggestion] = []
    missing: list[str] = []
    question: list[str] = []
    item: dict = {}
    texts: list[str] = []
    if section == "summary":
        texts = [content.get("summary") or ""]
        if not _substantive(texts[0]): missing.append("distinctive professional focus")
        elif len(_words(texts[0])) > 80: issues.append(ResumeIssue(type="too_long", message="The summary is longer than it needs to be."))
        else: strengths.append("The summary communicates a specific professional direction.")
    elif section in {"experience", "projects", "education"}:
        rows = content.get(section, [])
        if item_index is None: item_index = 0 if rows else None
        item = rows[item_index] if item_index is not None and item_index < len(rows) else {}
        if section == "experience": texts = item.get("bullets") or []
        else: texts = [item.get("description") or ""]
        if not texts or not any(_substantive(x) for x in texts):
            missing.append("specific work, contribution, or outcome")
        else: strengths.append("This section includes specific, usable detail.")
    else:
        texts = [x for g in content.get("skill_groups", []) for x in g.get("items", [])]
        if not texts: missing.append("verified skills")
        else: strengths.append("Skills are based on saved profile claims.")

    generic = [x for x in texts if x and (GENERIC.match(x.strip()) or not _substantive(x))]
    if generic:
        issues.append(ResumeIssue(type="too_vague", message="This content does not explain the work or contribution clearly."))
        suggestions.append(_suggestion(section, item_index, "remove_generic_content", "Needs detail",
            "Generic responsibility statements do not show what you actually did."))
    relevant = _rag_terms(rag, item)
    if relevant:
        suggestions.append(_suggestion(section, item_index, "add_existing_fact", "Relevant saved context",
            "CareerPilot found career context that may make this section more specific.", relevant[0],
            [ResumeEvidence(source_type="career_knowledge", domain=section, excerpt=relevant[0])], True))
    if missing:
        question = [_question(section, item, language)]
        suggestions.append(_suggestion(section, item_index, "ask_for_detail", "Missing information",
            "CareerPilot needs one concrete fact before it can write a strong, factual suggestion."))
    quality = "insufficient_information" if missing else ("needs_improvement" if issues else ("strong" if strengths and len(texts) > 1 else "good"))
    return ResumeSectionAnalysis(section=section, item_index=item_index, quality=quality,
        issues=issues, strengths=strengths, supported_suggestions=suggestions,
        missing_information=missing, clarification_questions=question)


def analyze_resume(content: dict, verified: dict, rag: list[str] | None = None) -> ResumeAnalysisResponse:
    analyses = [analyze_section(content, verified, "summary", rag=rag)]
    for section in ("experience", "projects", "education"):
        analyses.extend(analyze_section(content, verified, section, i, rag) for i in range(len(content.get(section, []))))
    analyses.append(analyze_section(content, verified, "skills", rag=rag))
    rank = {"insufficient_information": 0, "weak": 1, "needs_improvement": 2, "good": 3, "strong": 4}
    top = min(analyses, key=lambda x: rank[x.quality]) if analyses else None
    return ResumeAnalysisResponse(analyses=analyses, top_priority=top)


def apply_suggestion(content: dict, suggestion: ResumeSuggestion, edited_text: str | None = None) -> dict:
    text = (edited_text if edited_text is not None else suggestion.suggestion or "").strip()
    if not text:
        raise ValueError("This suggestion has no text to apply")
    result = deepcopy(content)
    if suggestion.section == "summary": result["summary"] = text
    elif suggestion.section == "experience":
        row = result["experience"][suggestion.item_index]
        if suggestion.bullet_index is None: row.setdefault("bullets", []).append(text)
        else: row["bullets"][suggestion.bullet_index] = text
    elif suggestion.section == "projects": result["projects"][suggestion.item_index]["description"] = text
    elif suggestion.section == "skills":
        groups = result.setdefault("skill_groups", [])
        if not groups:
            groups.append({"category": "Skills", "items": [], "visible": True})
        existing = {item.casefold() for group in groups for item in group.get("items", [])}
        if text.casefold() not in existing:
            groups[0].setdefault("items", []).append(text)
    else: raise ValueError("This suggestion type cannot be applied as text")
    return result


def validate_suggestion(suggestion: ResumeSuggestion, verified: dict, rag: list[str], user_answer: str | None = None) -> list[str]:
    text = suggestion.suggestion or ""
    evidence_text = " ".join([str(verified), *rag, user_answer or "", *(e.excerpt or "" for e in suggestion.evidence)]).casefold()
    errors = []
    for number in re.findall(r"\d+(?:\.\d+)?%?", text):
        if number.casefold() not in evidence_text:
            errors.append(f"unsupported numeric claim: {number}")
    if suggestion.requires_confirmation and not user_answer and not any(e.source_type == "profile" for e in suggestion.evidence):
        errors.append("suggestion requires user confirmation")
    return errors
