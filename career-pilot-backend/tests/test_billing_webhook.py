import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.session import get_db
from app.main import app


class FakeSession:
    def __init__(self):
        self.executed = 0
        self.committed = 0

    async def execute(self, _statement):
        self.executed += 1

    async def commit(self):
        self.committed += 1


def signature(payload: bytes, secret: str) -> str:
    timestamp = int(time.time())
    digest = hmac.new(secret.encode(), f"{timestamp}.".encode() + payload, hashlib.sha256)
    return f"t={timestamp},v1={digest.hexdigest()}"


def test_stripe_webhook_requires_valid_signature_and_persists_event(monkeypatch):
    secret = "whsec_test_secret"
    payload = json.dumps(
        {
            "id": "evt_test_1",
            "object": "event",
            "type": "checkout.session.completed",
            "livemode": False,
            "data": {"object": {"id": "cs_test_1"}},
        },
        separators=(",", ":"),
    ).encode()
    fake = FakeSession()

    async def override_db():
        yield fake

    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", secret)
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            invalid = client.post(
                "/api/v1/billing/webhook",
                content=payload,
                headers={"Stripe-Signature": "t=1,v1=invalid"},
            )
            accepted = client.post(
                "/api/v1/billing/webhook",
                content=payload,
                headers={"Stripe-Signature": signature(payload, secret)},
            )
    finally:
        app.dependency_overrides.clear()

    assert invalid.status_code == 400
    assert accepted.status_code == 200
    assert accepted.json() == {"received": True}
    assert fake.executed == 1 and fake.committed == 1


def test_stripe_webhook_is_disabled_without_secret(monkeypatch):
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", None)
    with TestClient(app) as client:
        response = client.post("/api/v1/billing/webhook", content=b"{}")
    assert response.status_code == 503
