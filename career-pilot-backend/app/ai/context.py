from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from uuid import UUID, uuid4

request_id_var: ContextVar[str | None] = ContextVar("ai_request_id", default=None)
user_id_var: ContextVar[UUID | None] = ContextVar("ai_user_id", default=None)
conversation_id_var: ContextVar[str | None] = ContextVar("ai_conversation_id", default=None)


@dataclass(frozen=True)
class AIContext:
    user_id: UUID | None
    request_id: str
    conversation_id: str | None


def current_ai_context() -> AIContext:
    request_id = request_id_var.get()
    if not request_id:
        request_id = uuid4().hex
        request_id_var.set(request_id)
    return AIContext(user_id_var.get(), request_id, conversation_id_var.get())


@contextmanager
def ai_user_id(user_id: UUID):
    token = user_id_var.set(user_id)
    try:
        yield
    finally:
        user_id_var.reset(token)


@contextmanager
def ai_conversation(conversation_id: str | None):
    token = conversation_id_var.set(conversation_id)
    try:
        yield
    finally:
        conversation_id_var.reset(token)
