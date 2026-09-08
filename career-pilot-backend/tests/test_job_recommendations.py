from datetime import UTC, datetime

from app.schemas.job import JobResult
from app.services.job_recommendations import CareerContext, rank_jobs


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
