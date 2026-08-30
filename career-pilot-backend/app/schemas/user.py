from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.common import ORMResponse


class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    is_active: bool = True


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: EmailStr | None = None
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class UserResponse(UserBase, ORMResponse):
    pass
