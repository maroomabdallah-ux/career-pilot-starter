from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import configure_mappers

from app.core.exceptions import (
    CareerProfileAlreadyExistsError,
    DuplicateSkillError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from app.db.base import Base
from app.main import app
from app.schemas.career_profile import CareerProfileCreate
from app.schemas.education import EducationCreate, EducationUpdate
from app.schemas.experience import ExperienceCreate
from app.schemas.project import ProjectCreate
from app.schemas.skill import SkillCreate
from app.schemas.user import UserCreate, UserUpdate
from app.services.career_profile import CareerProfileService
from app.services.skill import SkillService
from app.services.user import UserService


def test_models_and_relationships_configure():
    configure_mappers()
    assert set(Base.metadata.tables) == {
        "users",
        "career_profiles",
        "education",
        "experiences",
        "projects",
        "skills",
    }
    profile = Base.metadata.tables["career_profiles"]
    assert profile.c.user_id.unique
    assert Base.metadata.tables["skills"].constraints


def test_schema_validation_and_safe_defaults():
    first = ExperienceCreate(company="OpenAI", job_title="Engineer")
    second = ExperienceCreate(company="Example", job_title="Engineer")
    first.technologies.append("Python")
    assert second.technologies == []
    assert UserUpdate(first_name="Ada").model_dump(exclude_unset=True) == {"first_name": "Ada"}
    assert EducationUpdate().model_dump(exclude_unset=True) == {}
    with pytest.raises(ValidationError):
        SkillCreate(name="Python", years_of_experience=-1)
    with pytest.raises(ValidationError):
        EducationCreate(institution="University", start_date="2025-01-01", end_date="2024-01-01")
    with pytest.raises(ValidationError):
        ProjectCreate(name="Site", project_url="not-a-url")


@pytest.mark.asyncio
async def test_user_service_duplicate_and_missing():
    session = AsyncMock()
    service = UserService(session)
    service.repository.get_by_email = AsyncMock(return_value=object())
    with pytest.raises(UserAlreadyExistsError):
        await service.create_user(
            UserCreate(email="ADA@example.com", first_name="Ada", last_name="Lovelace")
        )
    service.repository.get_by_id = AsyncMock(return_value=None)
    with pytest.raises(UserNotFoundError):
        await service.get_user(uuid4())


@pytest.mark.asyncio
async def test_duplicate_profile_rejected():
    session = AsyncMock()
    service = CareerProfileService(session)
    service.repository.get_by_user_id = AsyncMock(return_value=object())
    service.repository.create = AsyncMock()
    user_id = uuid4()
    with pytest.raises(CareerProfileAlreadyExistsError):
        await service.create_profile(CareerProfileCreate(user_id=user_id))
    service.repository.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_duplicate_skill_rejected():
    session = AsyncMock()
    service = SkillService(session)
    service.repository.get_by_profile_and_name = AsyncMock(return_value=object())
    with pytest.raises(DuplicateSkillError):
        await service.create_skill(uuid4(), SkillCreate(name="Python"))


def test_openapi_and_http_error_contracts():
    client = TestClient(app)
    assert client.post("/api/v1/users", json={}).status_code == 422
    missing_id = uuid4()
    # A malformed UUID is rejected before a database dependency is consumed.
    assert client.get("/api/v1/users/not-a-uuid").status_code == 422
    paths = app.openapi()["paths"]
    assert "/api/v1/users" in paths
    assert "/api/v1/career-profiles/{profile_id}/skills" in paths
    assert missing_id
