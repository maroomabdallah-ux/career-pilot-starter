import asyncio
import os
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.session import AsyncSessionLocal
from app.main import app
from app.models.user import User

pytestmark = pytest.mark.skipif(
    not os.getenv("RUN_LIVE_RESUME_TESTS"),
    reason="requires migrated PostgreSQL, Chromium, and a valid OPENAI_API_KEY",
)


async def _delete_test_user(email: str):
    async with AsyncSessionLocal() as session:
        user_id = await session.scalar(select(User.id).where(User.email == email))
        if user_id:
            await session.execute(delete(User).where(User.id == user_id))
            await session.commit()


def test_authenticated_resume_generation_templates_persistence_and_pdf():
    email = f"resume-live-{uuid4().hex}@example.com"
    try:
        with TestClient(app) as client:
            signup = client.post(
                "/api/v1/auth/signup",
                json={
                    "email": email,
                    "password": "ResumeTest123!",
                    "first_name": "Test",
                    "last_name": "Candidate",
                },
            )
            assert signup.status_code == 201, signup.text
            headers = {"Authorization": f"Bearer {signup.json()['access_token']}"}
            assert (
                client.post(
                    "/api/v1/me/profile",
                    headers=headers,
                    json={
                        "professional_title": "Backend Developer",
                        "city": "Amman",
                        "country": "Jordan",
                    },
                ).status_code
                == 201
            )
            assert (
                client.post(
                    "/api/v1/me/experiences",
                    headers=headers,
                    json={
                        "company": "Example Co",
                        "job_title": "Backend Developer",
                        "start_date": "2025-01-01",
                        "is_current": True,
                        "description": "Built APIs using FastAPI and PostgreSQL.",
                        "technologies": ["FastAPI", "PostgreSQL"],
                    },
                ).status_code
                == 201
            )
            for name, category in (
                ("Python", "Programming Languages"),
                ("FastAPI", "Backend"),
                ("PostgreSQL", "Databases"),
            ):
                assert (
                    client.post(
                        "/api/v1/me/skills",
                        headers=headers,
                        json={"name": name, "category": category},
                    ).status_code
                    == 201
                )

            generated = client.post(
                "/api/v1/resumes/generate",
                headers=headers,
                json={"title": "Master Resume", "template_id": "ats_classic"},
            )
            assert generated.status_code == 201, generated.text
            resume = generated.json()
            resume_id = resume["id"]
            original_content = resume["content"]
            assert resume["template_id"] == "ats_classic"
            assert original_content["experience"][0]["company"] == "Example Co"
            assert original_content["experience"][0]["job_title"] == "Backend Developer"
            assert "2025-01-01" == original_content["experience"][0]["start_date"]

            changed = client.patch(
                f"/api/v1/resumes/{resume_id}",
                headers=headers,
                json={"template_id": "ats_modern"},
            )
            assert changed.status_code == 200, changed.text
            assert changed.json()["content"] == original_content
            reloaded = client.get(f"/api/v1/resumes/{resume_id}", headers=headers)
            assert reloaded.json()["template_id"] == "ats_modern"
            assert reloaded.json()["content"] == original_content

            for template_id in ("ats_classic", "ats_modern"):
                client.patch(
                    f"/api/v1/resumes/{resume_id}",
                    headers=headers,
                    json={"template_id": template_id},
                )
                pdf = client.post(f"/api/v1/resumes/{resume_id}/export", headers=headers)
                assert pdf.status_code == 200, pdf.text
                assert pdf.headers["content-type"] == "application/pdf"
                assert pdf.content.startswith(b"%PDF-")
    finally:
        asyncio.run(_delete_test_user(email))
