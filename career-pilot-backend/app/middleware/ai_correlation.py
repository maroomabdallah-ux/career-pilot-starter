import re
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware

from app.ai.context import request_id_var

SAFE_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


class AIRequestCorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        supplied = request.headers.get("X-Request-ID", "")
        request_id = supplied if SAFE_ID.fullmatch(supplied) else uuid4().hex
        token = request_id_var.set(request_id)
        try:
            response = await call_next(request)
            if "X-Request-ID" not in response.headers:
                response.headers["X-Request-ID"] = request_id
            return response
        finally:
            request_id_var.reset(token)
