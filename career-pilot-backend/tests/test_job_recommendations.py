from datetime import UTC, datetime

from app.schemas.job import JobResult
from app.services.job_recommendations import (
    CareerContext,
    expand_search_roles,
    rank_jobs,
)


def listing(title, description):
    return JobResult(
        external_id=title,
        title=title,
        company="Example",
        source="Google Jobs",
        source_url="https://example.com",
        apply_url="https://example.com",
        description=description,
        retrieved_at=datetime.now(UTC),
    )


def test_ranking_is_deterministic_and_gaps_are_from_description():
    context = CareerContext(roles=["Python Developer"], skills=["Python", "FastAPI"])
    rows = [
        listing("Java Developer", "Java and Kubernetes"),
        listing("Python Developer", "Python FastAPI AWS"),
    ]
    first = rank_jobs(rows, context)
    assert first[0].title == "Python Developer"
    score = first[0].match_score
    assert rank_jobs(rows, context)[0].match_score == score
    assert first[0].skill_gaps == ["AWS"]
    assert first[0].matched_skills == ["Python", "FastAPI"]


def test_empty_context_has_no_fake_match_and_keeps_jobs():
    result = rank_jobs([listing("Developer", "Python")], CareerContext())
    assert len(result) == 1
    assert result[0].match_score is None
    assert result[0].skill_gaps == []


def test_other_user_scores_do_not_mutate_shared_candidates():
    shared = listing("Python Developer", "Python AWS")
    private = shared.model_copy(deep=True)
    rank_jobs([private], CareerContext(skills=["Python"]))
    assert shared.match_score is None
    assert shared.matched_skills == []


def test_role_expansion_is_profile_driven_and_domain_neutral():
    nurse = expand_search_roles(CareerContext(roles=["Registered Nurse"], skills=["Triage"]))
    accountant = expand_search_roles(
        CareerContext(roles=["Accountant"], skills=["Accounts Payable"])
    )
    marketing = expand_search_roles(CareerContext(roles=["Marketing Specialist"], skills=["SEO"]))

    assert nurse == ["Registered Nurse", "Triage Registered Nurse"]
    assert accountant == ["Accountant", "Accounts Payable Accountant"]
    assert marketing == ["Marketing Specialist", "SEO Marketing Specialist"]
    assert all("developer" not in role.casefold() for role in nurse + accountant + marketing)
