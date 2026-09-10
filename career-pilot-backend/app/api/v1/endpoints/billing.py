import json

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.dialects.postgresql import insert
from stripe import SignatureVerificationError, Webhook

from app.api.dependencies import SessionDep
from app.core.config import settings
from app.models.billing import StripeWebhookEvent

router = APIRouter()


@router.post("/webhook")
async def stripe_webhook(request: Request, session: SessionDep):
    secret = settings.STRIPE_WEBHOOK_SECRET
    if not secret:
        raise HTTPException(503, "Stripe webhook is not configured")
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(400, "Missing Stripe-Signature header")
    payload = await request.body()
    try:
        event = Webhook.construct_event(payload, signature, secret)
    except (ValueError, SignatureVerificationError) as exc:
        raise HTTPException(400, "Invalid Stripe webhook signature") from exc
    values = json.loads(str(event))
    await session.execute(
        insert(StripeWebhookEvent)
        .values(
            event_id=values["id"],
            event_type=values["type"],
            livemode=bool(values.get("livemode")),
            payload=values,
        )
        .on_conflict_do_nothing(index_elements=["event_id"])
    )
    await session.commit()
    return {"received": True}
