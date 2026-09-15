from app.services.cv_onboarding import parse_cv_text


def test_cv_extraction_maps_canonical_sections_without_writing():
    review = parse_cv_text(
        """Sam Example
Registered Nurse
sam@example.com
Education
University of Jordan — Bachelor of Nursing
Skills
Patient Care, Triage, Clinical Documentation
Experience
Clinical Nurse at City Hospital
Projects
Community health outreach
Certifications
Basic Life Support
"""
    )

    assert review.professional_title == "Registered Nurse"
    assert review.education[0].institution.startswith("University")
    assert "Triage" in review.skills
    assert review.experiences[0].company == "City Hospital"
    assert review.projects[0].name == "Community health outreach"
    assert review.certifications == ["Basic Life Support"]


def test_cv_reports_only_missing_required_profile_fields():
    review = parse_cv_text("Taylor\nMarketing Coordinator\nSkills\nCampaign planning")

    assert review.missing_fields == ["education"]


def test_parser_handles_descriptive_cv_section_headings_and_dated_roles():
    review = parse_cv_text(
        """Maroom Abdalla
FULL-STACK DEVELOPER | AI AGENT DEVELOPER
Amman, Jordan | +962 79 002 6786
TECHNICAL SKILLS
Programming: Python, Java, JavaScript
Backend: FastAPI, REST APIs
PROFESSIONAL EXPERIENCE
Full-Stack & AI Development Trainee | Ebtikar AI - Amman | Jul 2026 - Present
- Built applications with Python and FastAPI.
Backend Software Engineering Intern | Acabes Jordan - Amman | Sep 2025 - Jan 2026
SELECTED PROJECTS
CareerPilot AI - In Progress | Python, FastAPI, React
- Building an AI-powered career assistant.
EDUCATION
Bachelor of Computer Science | The World Islamic Sciences and Education University, Jordan
COURSES & DEVELOPMENT
- Full Stack Web Development Course
"""
    )

    assert review.city == "Amman"
    assert review.country == "Jordan"
    assert {"Python", "FastAPI", "REST APIs"}.issubset(review.skills)
    assert [item.company for item in review.experiences] == ["Ebtikar AI", "Acabes Jordan"]
    assert review.projects[0].name == "CareerPilot AI - In Progress"
    assert review.education[0].institution.startswith("The World Islamic")
    assert review.experiences[0].start_date.isoformat() == "2026-07-01"
    assert review.experiences[0].is_current is True
    assert review.experiences[1].end_date.isoformat() == "2026-01-01"
