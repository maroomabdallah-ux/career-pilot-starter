"""Durable request claims: a process crash never silently reruns an AI workflow."""

import hashlib
import json
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException
from fastapi.routing import APIRoute
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from starlette.responses import JSONResponse

from app.ai.context import request_id_var
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.application import IdempotentRequest
from app.models.user import User


class IdempotentRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()

        async def handler(request):
            # Binary PDF generation has no persistent side effects and is not replayed here.
            if request.method not in {"POST", "PATCH", "DELETE"} or request.url.path.endswith(
                "/export"
            ):
                return await original(request)
            key = request.headers.get("Idempotency-Key")
            if not key:
                # Legacy clients stay compatible. First-party clients always supply a key.
                return await original(request)
            if (
                not 8 <= len(key) <= 128
                or not key.isascii()
                or not all(c.isalnum() or c in "-_" for c in key)
            ):
                raise HTTPException(422, "Invalid Idempotency-Key")
            auth = request.headers.get("Authorization", "")
            try:
                if not auth.lower().startswith("bearer "):
                    raise ValueError()
                user_id = UUID(decode_token(auth.split(" ", 1)[1], "access")["sub"])
            except (jwt.PyJWTError, KeyError, ValueError):
                raise HTTPException(401, "Authentication required") from None
            body = await request.body()
            try:
                canonical = json.dumps(json.loads(body), sort_keys=True, separators=(",", ":"))
            except (ValueError, UnicodeDecodeError):
                canonical = body.hex()
            fingerprint = hashlib.sha256((request.url.query + canonical).encode()).hexdigest()
            operation = f"{request.method} {request.url.path}"
            request_id = request_id_var.get() or uuid4().hex
            async with AsyncSessionLocal() as session:
                user = await session.get(User, user_id)
                if not user or not user.is_active:
                    raise HTTPException(401, "Authentication required")
                claimed = await session.scalar(
                    insert(IdempotentRequest)
                    .values(
                        user_id=user_id,
                        operation=operation,
                        key=key,
                        fingerprint=fingerprint,
                        request_id=request_id,
                    )
                    .on_conflict_do_nothing(constraint="uq_idempotency_user_operation_key")
                    .returning(IdempotentRequest.id)
                )
                await session.commit()
                record = await session.scalar(
                    select(IdempotentRequest).where(
                        IdempotentRequest.user_id == user_id,
                        IdempotentRequest.operation == operation,
                        IdempotentRequest.key == key,
                    )
                )
                if record.fingerprint != fingerprint:
                    raise HTTPException(409, "This idempotency key was used with different data.")
                if not claimed:
                    if record.state == "completed":
                        return JSONResponse(
                            record.response,
                            status_code=record.status_code,
                            headers={
                                "Idempotency-Replayed": "true",
                                "X-Request-ID": record.request_id,
                            },
                        )
                    raise HTTPException(
                        409,
                        {
                            "message": "This action is processing or needs reconciliation. Do not repeat it with a new key.",
                            "request_id": record.request_id,
                        },
                        headers={"Retry-After": "3"},
                    )
            token = request_id_var.set(request_id)
            try:
                try:
                    response = await original(request)
                except HTTPException as exc:
                    response = JSONResponse(
                        {"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers
                    )
                payload = json.loads(response.body or b"null")
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(IdempotentRequest)
                        .where(IdempotentRequest.id == claimed)
                        .values(
                            state="completed", status_code=response.status_code, response=payload
                        )
                    )
                    await session.commit()
                response.headers["X-Request-ID"] = request_id
                return response
            finally:
                # Unexpected errors leave a durable processing claim for reconciliation.
                request_id_var.reset(token)

        return handler
