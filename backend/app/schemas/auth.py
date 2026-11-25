from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=2, max_length=200)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str
    role: str
    onboarding_step: int
    onboarding_completed: bool


class UserMeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    onboarding_step: int
    onboarding_completed: bool

    model_config = {"from_attributes": True}


class OnboardingProgressUpdate(BaseModel):
    onboarding_step: int = Field(ge=1, le=6)
    onboarding_completed: Optional[bool] = None
