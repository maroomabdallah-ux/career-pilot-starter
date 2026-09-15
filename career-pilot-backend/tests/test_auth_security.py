from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import create_access_token, decode_token, hash_password, verify_password
from app.main import app
from app.schemas.auth import SignupRequest


def test_password_hash_and_token_helpers():
    hashed = hash_password("Career123")
    assert hashed != "Career123"
    assert verify_password("Career123", hashed)
    assert not verify_password("Wrong123", hashed)
    user_id = uuid4()
    token = create_access_token(user_id)
    assert decode_token(token, "access")["sub"] == str(user_id)
    with pytest.raises(jwt.InvalidTokenError):
        decode_token(token, "refresh")


def test_password_policy_and_protected_route_contract():
    with pytest.raises(ValueError):
        SignupRequest(
            email="user@example.com", password="onlyletters", first_name="A", last_name="B"
        )
    with pytest.raises(ValueError):
        SignupRequest(
            email="user@example.com", password="Password1", first_name="A", last_name="B"
        )
    client = TestClient(app)
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/me/profile").status_code == 401
    schemas = app.openapi()["components"]["schemas"]
    assert "password_hash" not in schemas["UserResponse"]["properties"]


def test_failed_refresh_removes_the_browser_cookie():
    client = TestClient(app)
    client.cookies.set(settings.REFRESH_COOKIE_NAME, "stale-or-invalid")

    response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert f'{settings.REFRESH_COOKIE_NAME}=""' in response.headers["set-cookie"]
    assert "Max-Age=0" in response.headers["set-cookie"]
