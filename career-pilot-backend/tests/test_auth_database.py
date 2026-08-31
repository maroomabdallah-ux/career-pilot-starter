import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_DATABASE_TESTS"), reason="requires a migrated PostgreSQL test database"
)


def signup(client: TestClient, label: str):
    return client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"{label}-{uuid4().hex}@example.com",
            "password": "Career123",
            "first_name": label,
            "last_name": "Tester",
        },
    )


def test_auth_rotation_logout_and_multi_user_ownership():
    with TestClient(app) as user_a, TestClient(app) as user_b:
        created_a = signup(user_a, "alpha")
        assert created_a.status_code == 201, created_a.text
        assert "password_hash" not in created_a.text
        token_a = created_a.json()["access_token"]
        headers_a = {"Authorization": f"Bearer {token_a}"}
        assert user_a.get("/api/v1/auth/me", headers=headers_a).status_code == 200
        assert (
            user_a.post(
                "/api/v1/me/profile", headers=headers_a, json={"professional_title": "Engineer"}
            ).status_code
            == 201
        )
        education = user_a.post(
            "/api/v1/me/education", headers=headers_a, json={"institution": "University"}
        )
        assert education.status_code == 201, education.text

        created_b = signup(user_b, "beta")
        token_b = created_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        assert (
            user_b.post(
                "/api/v1/me/profile", headers=headers_b, json={"professional_title": "Designer"}
            ).status_code
            == 201
        )
        forbidden = user_b.patch(
            f"/api/v1/me/education/{education.json()['id']}",
            headers=headers_b,
            json={"institution": "Stolen"},
        )
        assert forbidden.status_code == 403

        old_refresh = user_a.cookies.get(settings.REFRESH_COOKIE_NAME)
        refreshed = user_a.post("/api/v1/auth/refresh")
        assert refreshed.status_code == 200
        assert user_a.cookies.get(settings.REFRESH_COOKIE_NAME) != old_refresh
        replay = TestClient(app)
        replay.cookies.set(settings.REFRESH_COOKIE_NAME, old_refresh)
        assert replay.post("/api/v1/auth/refresh").status_code == 401

        assert user_a.post("/api/v1/auth/logout").status_code == 204
        assert user_a.post("/api/v1/auth/refresh").status_code == 401


def test_duplicate_email_invalid_login_and_invalid_token():
    with TestClient(app) as client:
        email = f"duplicate-{uuid4().hex}@example.com"
        payload = {
            "email": email,
            "password": "Career123",
            "first_name": "Test",
            "last_name": "User",
        }
        assert client.post("/api/v1/auth/signup", json=payload).status_code == 201
        assert client.post("/api/v1/auth/signup", json=payload).status_code == 409
        assert (
            client.post(
                "/api/v1/auth/login", json={"email": email, "password": "Wrong123"}
            ).status_code
            == 401
        )
        assert (
            client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid"}).status_code
            == 401
        )
