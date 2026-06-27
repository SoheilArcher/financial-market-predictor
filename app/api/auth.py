import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.subscription import Plan, Subscription
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, ResendVerificationRequest, TokenResponse, UserResponse
from app.services.emailer import send_verification_email
from app.services.security import create_access_token, decode_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_session():
    async with AsyncSessionLocal() as session:
        yield session


def to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        country=user.country,
        email_verified=bool(user.email_verified_at),
        role=user.role,
        status=user.status,
        referral_code=user.referral_code,
        referred_by_user_id=user.referred_by_user_id,
    )


def _new_email_token() -> str:
    return secrets.token_urlsafe(48)


def _normalize_referral_code(code: str | None) -> str | None:
    normalized = (code or "").strip().upper().replace(" ", "")
    return normalized or None


async def _new_referral_code(session: AsyncSession) -> str:
    for _ in range(12):
        code = secrets.token_urlsafe(6).replace("-", "").replace("_", "").upper()[:8]
        existing = await session.scalar(select(User.id).where(User.referral_code == code))
        if existing is None:
            return code
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not generate referral code")


def _verification_url(token: str) -> str:
    base_url = settings.app_base_url.rstrip("/")
    return f"{base_url}/auth/verify-email?token={token}"


async def _issue_verification_email(session: AsyncSession, user: User) -> None:
    user.email_verification_token = _new_email_token()
    user.email_verification_sent_at = datetime.now(timezone.utc)
    await session.commit()
    await send_verification_email(user.email, _verification_url(user.email_verification_token))


async def _grant_free_registration_day(session: AsyncSession, user: User) -> None:
    existing_subscription = await session.scalar(
        select(Subscription).where(Subscription.user_id == user.id)
    )
    if existing_subscription is not None:
        return

    free_plan = await session.scalar(select(Plan).where(Plan.code == "free"))
    if free_plan is None:
        free_plan = Plan(
            code="free",
            name="Free",
            price=0,
            currency="USD",
            interval_days=30,
            max_analyses_per_day=10,
            allowed_timeframes=["5m", "15m"],
            status="active",
        )
        session.add(free_plan)
        await session.flush()

    now = datetime.now(timezone.utc)
    session.add(
        Subscription(
            user_id=user.id,
            plan_id=free_plan.id,
            status="active",
            starts_at=now,
            ends_at=now + timedelta(days=1),
        )
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await session.get(User, user_id)
    if user is None or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is not active",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_session)):
    email = payload.email.strip().lower()
    existing_user = await session.scalar(select(User).where(User.email == email))
    if existing_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    referral_code = _normalize_referral_code(payload.referral_code)
    referrer = None
    if referral_code:
        referrer = await session.scalar(select(User).where(User.referral_code == referral_code))
        if referrer is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid referral code")

    user_count = await session.scalar(select(func.count(User.id)))
    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        country=payload.country,
        referral_code=await _new_referral_code(session),
        referred_by_user_id=referrer.id if referrer else None,
        role="admin" if user_count == 0 else "user",
        status="active" if user_count == 0 else "pending_email",
        email_verified_at=datetime.now(timezone.utc) if user_count == 0 else None,
    )
    session.add(user)
    await session.flush()
    if user.status == "active":
        await _grant_free_registration_day(session, user)
    await session.commit()
    await session.refresh(user)
    if user.status == "pending_email":
        await _issue_verification_email(session, user)

    token = create_access_token(str(user.id), {"role": user.role})
    return TokenResponse(access_token=token, user=to_user_response(user))


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)):
    email = payload.email.strip().lower()
    user = await session.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.status == "pending_email" or not user.email_verified_at:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Please verify your email before login")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    token = create_access_token(str(user.id), {"role": user.role})
    return TokenResponse(access_token=token, user=to_user_response(user))


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)):
    return to_user_response(current_user)


@router.post("/resend-verification")
async def resend_verification(payload: ResendVerificationRequest, session: AsyncSession = Depends(get_session)):
    email = payload.email.strip().lower()
    user = await session.scalar(select(User).where(User.email == email))
    if user is None:
        return {"sent": True}
    if user.email_verified_at and user.status == "active":
        return {"sent": False, "detail": "Email is already verified"}
    last_sent = user.email_verification_sent_at
    if last_sent and last_sent.tzinfo is None:
        last_sent = last_sent.replace(tzinfo=timezone.utc)
    if last_sent and datetime.now(timezone.utc) - last_sent < timedelta(minutes=2):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Please wait before requesting another email")
    await _issue_verification_email(session, user)
    return {"sent": True}


@router.get("/verify-email", response_class=HTMLResponse)
async def verify_email(token: str, session: AsyncSession = Depends(get_session)):
    user = await session.scalar(select(User).where(User.email_verification_token == token))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid verification token")

    sent_at = user.email_verification_sent_at
    if sent_at and sent_at.tzinfo is None:
        sent_at = sent_at.replace(tzinfo=timezone.utc)
    if sent_at and datetime.now(timezone.utc) - sent_at > timedelta(hours=settings.email_verification_expire_hours):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification link has expired")

    user.email_verified_at = datetime.now(timezone.utc)
    user.email_verification_token = None
    user.status = "active"
    await _grant_free_registration_day(session, user)
    await session.commit()
    return """
    <html lang="fa" dir="rtl">
      <body style="font-family:Tahoma,Arial;background:#0b0f16;color:#f3f7fb;padding:32px">
        <h2>ایمیل شما تایید شد.</h2>
        <p>حساب کاربری فعال شد. حالا می‌توانید وارد Market AI شوید.</p>
        <a style="color:#58a6ff" href="/app">بازگشت به برنامه</a>
      </body>
    </html>
    """
