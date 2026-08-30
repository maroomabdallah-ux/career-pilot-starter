from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class ORMResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime
    updated_at: datetime


class DateRangeMixin(BaseModel):
    @model_validator(mode="after")
    def validate_date_range(self) -> Any:
        start: date | None = getattr(self, "start_date", None)
        end: date | None = getattr(self, "end_date", None)
        if start and end and end < start:
            raise ValueError("end_date must be on or after start_date")
        return self
