import pytest
from pydantic import ValidationError

from app.agents.resume.service import validate_fixed_facts
from app.schemas.resume import ResumeDraft, ResumeRegenerate
from app.services.resume_context import evaluate_resume_readiness
from app.services.resume_templates import TemplateAccessService, get_template, render_resume_html


class Profile:
    education = [object()]
    experiences = []
    projects = [object()]
    skills = [object()]


def test_regenerate_section_request_contract():
    for section in ("summary", "experience", "projects", "skills"):
        assert ResumeRegenerate.model_validate({"section": section}).section.value == section

    with pytest.raises(ValidationError) as missing:
        ResumeRegenerate.model_validate({})
    assert missing.value.errors()[0]["loc"] == ("section",)
    assert missing.value.errors()[0]["type"] == "missing"


def test_resume_editor_fields_and_section_order_round_trip():
    draft = ResumeDraft.model_validate(
        {
            "header": {"full_name": "A User", "email": "a@example.com"},
            "summary": "Builds **reliable** products.",
            "education": [{"institution": "University", "description": "Honors"}],
            "projects": [{"name": "Portal", "bullets": ["Built the API"]}],
            "skill_groups": [{"category": "Backend", "items": ["Python"]}],
            "section_order": ["summary", "projects", "experience", "skills", "education"],
        }
    )
    saved = draft.model_dump()
    assert saved["summary"] == "Builds **reliable** products."
    assert saved["education"][0]["description"] == "Honors"
    assert saved["projects"][0]["bullets"] == ["Built the API"]
    assert saved["section_order"][1] == "projects"


def test_fresh_graduate_readiness_uses_education_projects_and_skills():
    readiness = evaluate_resume_readiness(Profile())
    assert readiness["ready"] is True
    assert readiness["career_stage"] == "student"


def test_unknown_template_falls_back_to_careerpilot_classic():
    assert get_template("not-real")["id"] == "careerpilot_classic"


def test_all_current_templates_can_preview_and_export_for_free_users():
    access = TemplateAccessService()
    user = object()
    assert access.can_preview("premium_minimal") is True
    assert access.can_export("premium_minimal", user) is True
    assert access.can_export("ats_modern", user) is True


def test_fixed_fact_validator_rejects_seniority_and_date_changes():
    source = {
        "header": {"full_name": "A User", "email": "a@example.com"},
        "experience": [
            {
                "company": "Acme",
                "job_title": "Developer",
                "start_date": "2024-01-01",
                "end_date": None,
            }
        ],
        "education": [],
        "projects": [],
        "skills": [],
    }
    changed = {
        "header": {"full_name": "A User", "email": "a@example.com"},
        "experience": [
            {
                "company": "Acme",
                "job_title": "Senior Developer",
                "start_date": "2023-01-01",
                "end_date": None,
            }
        ],
        "education": [],
        "projects": [],
        "skill_groups": [],
    }
    errors = validate_fixed_facts(source, changed)
    assert any("job_title" in error for error in errors)
    assert any("start_date" in error for error in errors)


def test_html_export_is_a4_text_and_links():
    html = render_resume_html(
        {
            "header": {
                "full_name": "A User",
                "email": "a@example.com",
                "linkedin": "https://example.com",
            },
            "summary": "Backend developer",
            "section_order": ["summary"],
        },
        "ats_classic",
    )
    assert "@page{size:A4" in html
    assert "Backend developer" in html
    assert '<a href="https://example.com">' in html


def test_html_export_preserves_safe_rich_text_and_project_bullets():
    html = render_resume_html(
        {
            "header": {"full_name": "A User", "email": "a@example.com"},
            "summary": "Builds **reliable** and __accessible__ products.",
            "projects": [
                {
                    "name": "Portal",
                    "bullets": ["Improved **keyboard navigation**"],
                    "project_url": "https://example.com/project",
                }
            ],
            "section_order": ["summary", "projects"],
        },
        "careerpilot_classic",
    )
    assert "<strong>reliable</strong>" in html
    assert "<em>accessible</em>" in html
    assert "<li>Improved <strong>keyboard navigation</strong></li>" in html
    assert '<a href="https://example.com/project">Project</a>' in html
