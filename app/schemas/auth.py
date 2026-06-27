from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str = Field(min_length=5, max_length=255)
    password: str = Field(min_length=8, max_length=128)
    full_name: str | None = Field(default=None, max_length=120)
    country: str | None = Field(default=None, max_length=80)
    referral_code: str | None = Field(default=None, max_length=40)


class LoginRequest(BaseModel):
    email: str
    password: str


class ResendVerificationRequest(BaseModel):
    email: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str | None
    country: str | None
    email_verified: bool
    role: str
    status: str
    referral_code: str | None = None
    referred_by_user_id: int | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
