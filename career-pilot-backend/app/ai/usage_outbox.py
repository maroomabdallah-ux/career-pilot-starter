"""Durable accounting delivery. Replay with: python -m app.ai.usage_outbox.

The configured directory must live on a persistent volume in production.
Only accounting metadata is stored; prompts and provider secrets are excluded.
"""

import asyncio
import hashlib
import json
import logging
import os
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.ai_usage import AIUsage

logger = logging.getLogger(__name__)
FIELDS = [
    column.name
    for column in AIUsage.__table__.columns
    if column.name not in {"id", "created_at", "updated_at"}
]


def write_event(payload):
    root = Path(settings.AI_USAGE_OUTBOX_DIR)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    # Include the payload hash: a later successful completion can upgrade a failed event.
    serialized = json.dumps(payload, sort_keys=True, default=str)
    path = root / (hashlib.sha256(serialized.encode()).hexdigest() + ".json")
    temporary = root / (path.name + f".{os.getpid()}.{os.urandom(8).hex()}.tmp")
    with temporary.open("x", encoding="utf-8") as stream:
        os.chmod(temporary, 0o600)
        stream.write(serialized)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)
    directory = os.open(root, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)
    return path


async def deliver(payload):
    payload = dict(payload)
    payload["user_id"] = UUID(str(payload["user_id"]))
    for key in ("input_cost", "cached_input_cost", "output_cost", "total_cost"):
        if payload.get(key) is not None:
            payload[key] = Decimal(str(payload[key]))
    statement = insert(AIUsage).values(**payload)
    # Callback replay is a no-op. A successful event may replace a failed/missing one.
    statement = statement.on_conflict_do_update(
        constraint="uq_ai_usage_user_call",
        set_={key: getattr(statement.excluded, key) for key in FIELDS},
        where=AIUsage.pricing_status.in_(["failed_llm_request", "missing_provider_usage"])
        & (statement.excluded.total_tokens > AIUsage.total_tokens),
    )
    async with AsyncSessionLocal() as session:
        await session.execute(statement)
        await session.commit()
        return await session.scalar(
            select(AIUsage).where(
                AIUsage.user_id == payload["user_id"], AIUsage.llm_call_id == payload["llm_call_id"]
            )
        )


async def persist_usage(item):
    payload = {key: getattr(item, key) for key in FIELDS}
    path = await asyncio.to_thread(write_event, payload)
    for attempt in range(3):
        try:
            result = await deliver(payload)
            path.unlink(missing_ok=True)
            return result
        except Exception:
            if attempt < 2:
                await asyncio.sleep(0.1 * (attempt + 1))
    logger.error("AI usage queued for replay", extra={"llm_call_id": item.llm_call_id})
    return None


async def replay():
    delivered, pending = 0, 0
    for path in Path(settings.AI_USAGE_OUTBOX_DIR).glob("*.json"):
        try:
            await deliver(json.loads(path.read_text()))
            path.unlink(missing_ok=True)
            delivered += 1
        except Exception:
            pending += 1
    return {"delivered": delivered, "pending": pending}


if __name__ == "__main__":
    print(asyncio.run(replay()))
