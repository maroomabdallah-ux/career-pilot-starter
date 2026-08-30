import os

import pytest
from fastapi.testclient import TestClient

from app.main import app

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_DATABASE_TESTS"), reason="requires a migrated PostgreSQL test database"
)


def test_complete_career_profile_crud():
    with TestClient(app) as client:
        user_response = client.post(
            "/api/v1/users",
            json={"email": "core-crud@example.com", "first_name": "Core", "last_name": "Test"},
        )
        assert user_response.status_code == 201, user_response.text
        user = user_response.json()
        assert client.get(f"/api/v1/users/{user['id']}").status_code == 200
        assert (
            client.patch(f"/api/v1/users/{user['id']}", json={"first_name": "Updated"}).json()[
                "first_name"
            ]
            == "Updated"
        )
        assert (
            client.post(
                "/api/v1/users",
                json={"email": "CORE-CRUD@example.com", "first_name": "Core", "last_name": "Test"},
            ).status_code
            == 409
        )

        profile_response = client.post(
            "/api/v1/career-profiles",
            json={"user_id": user["id"], "professional_title": "Backend Engineer"},
        )
        assert profile_response.status_code == 201, profile_response.text
        profile = profile_response.json()
        profile_id = profile["id"]
        assert (
            client.post(
                "/api/v1/career-profiles",
                json={"user_id": user["id"]},
            ).status_code
            == 409
        )

        resources = [
            ("education", {"institution": "University"}),
            ("experiences", {"company": "Example", "job_title": "Engineer"}),
            ("projects", {"name": "CareerPilot", "technologies": ["Python"]}),
            ("skills", {"name": "Python", "years_of_experience": 5}),
        ]
        for path, payload in resources:
            response = client.post(f"/api/v1/career-profiles/{profile_id}/{path}", json=payload)
            assert response.status_code == 201, response.text

        assert (
            client.post(
                f"/api/v1/career-profiles/{profile_id}/skills", json={"name": "python"}
            ).status_code
            == 409
        )
        full_profile = client.get(f"/api/v1/career-profiles/{profile_id}").json()
        assert len(full_profile["education"]) == 1
        assert len(full_profile["experiences"]) == 1
        assert len(full_profile["projects"]) == 1
        assert len(full_profile["skills"]) == 1
        assert client.get(f"/api/v1/users/{'0' * 32}").status_code == 404
        assert client.delete(f"/api/v1/users/{user['id']}").status_code == 204
