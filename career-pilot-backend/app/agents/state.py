from typing import TypedDict


class CareerState(TypedDict, total=False):
    user_id: str
    message: str
    current_step: str
    result: dict
