from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.auth import UserResponse


class UserUpdateRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    role: str | None = Field(default=None, pattern="^(admin|user)$")
    status: str | None = Field(default=None, pattern="^(active|blocked)$")


class PlanCreateRequest(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=80)
    price: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="USD", max_length=10)
    interval_days: int = Field(default=30, ge=1, le=3660)
    max_analyses_per_day: int = Field(default=20, ge=0)
    allowed_timeframes: list[str] = Field(default_factory=list)
    status: str = Field(default="active", pattern="^(active|inactive)$")


class PlanUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    price: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, max_length=10)
    interval_days: int | None = Field(default=None, ge=1, le=3660)
    max_analyses_per_day: int | None = Field(default=None, ge=0)
    allowed_timeframes: list[str] | None = None
    status: str | None = Field(default=None, pattern="^(active|inactive)$")


class PlanResponse(BaseModel):
    id: int
    code: str
    name: str
    price: Decimal
    currency: str
    interval_days: int
    max_analyses_per_day: int
    allowed_timeframes: list[str]
    status: str


class AssignSubscriptionRequest(BaseModel):
    plan_code: str = Field(min_length=2, max_length=40)
    days: int | None = Field(default=None, ge=1, le=3660)


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    plan: PlanResponse
    status: str
    starts_at: datetime
    ends_at: datetime


class UserWithSubscriptionResponse(UserResponse):
    subscription: SubscriptionResponse | None = None

