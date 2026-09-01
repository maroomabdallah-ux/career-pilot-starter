from app.agents.resume.service import merge_writing, unsupported_numbers
from app.schemas.resume import ExperienceWriting, ResumeWriting


def test_rejects_unsupported_resume_metrics():
    source = {"experience": [{"company": "Acme", "description": "Built APIs"}]}
    writing = ResumeWriting(
        experience=[ExperienceWriting(index=0, bullets=["Improved performance by 40%"])]
    )
    assert unsupported_numbers(source, writing) == {"40%"}


def test_section_regeneration_preserves_other_sections():
    base = {
        "summary": "Original",
        "experience": [{"company": "Acme", "job_title": "Developer", "bullets": ["Old"]}],
        "projects": [{"name": "Portal", "description": "Original project"}],
        "skills": ["Python"],
    }
    writing = ResumeWriting(experience=[ExperienceWriting(index=0, bullets=["Developed APIs"])])
    result = merge_writing(base, writing, "experience")
    assert result["experience"][0]["bullets"] == ["Developed APIs"]
    assert result["summary"] == "Original"
    assert result["projects"] == base["projects"]


def test_skill_groups_cannot_add_unsaved_skills():
    base = {"skills": ["Python"], "experience": [], "projects": []}
    result = merge_writing(
        base, ResumeWriting(skill_groups={"Backend": ["Python", "Kubernetes"]}), "skills"
    )
    assert result["skill_groups"] == {"Backend": ["Python"]}
