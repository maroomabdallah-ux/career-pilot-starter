import re

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.schemas.user import UserResponse


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_password(self):
        if not re.search(r"[A-Za-z]", self.password) or not re.search(r"\d", self.password):
            raise ValueError("Password must contain at least one letter and one number")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
