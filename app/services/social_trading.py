from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import SignalRecord
from app.models.social import AnalystFollow, AnalystProfile, PortfolioSetting, SharedAnalysis
from app.models.user import User
from app.services.signal_journal import evaluate_record


def _public_id_from_user(user: User) -> str:
    prefix = (user.full_name or user.email.split("@")[0]).lower()
    prefix = re.sub(r"[^a-z0-9]+", "-", prefix).strip("-") or "analyst"
    return f"{prefix}-{user.id}"


async def get_or_create_profile(session: AsyncSession, user: User) -> AnalystProfile:
    profile = await session.scalar(select(AnalystProfile).where(AnalystProfile.user_id == user.id))
    if profile:
        return profile
    profile = AnalystProfile(
        user_id=user.id,
        public_id=_public_id_from_user(user),
        display_name=user.full_name or user.email.split("@")[0],
        market_focus="iran" if user.country == "IR" else "crypto",
    )
    session.add(profile)
    await session.commit()
    await session.refresh(profile)
    return profile


async def upsert_profile(
    session: AsyncSession,
    user: User,
    display_name: str | None,
    bio: str | None,
    market_focus: str | None,
    is_public: bool = True,
) -> AnalystProfile:
    profile = await get_or_create_profile(session, user)
    if display_name:
        profile.display_name = display_name[:120]
    profile.bio = bio[:1000] if bio else None
    if market_focus:
        profile.market_focus = market_focus[:40]
    profile.is_public = is_public
    await session.commit()
    await session.refresh(profile)
    return profile


async def follower_count(session: AsyncSession, analyst_user_id: int) -> int:
    return int(await session.scalar(select(func.count(AnalystFollow.id)).where(AnalystFollow.analyst_user_id == analyst_user_id)) or 0)


async def publish_latest_signal(
    session: AsyncSession,
    user: User,
    signal_record_id: int | None,
    title: str | None,
    note: str | None,
) -> SharedAnalysis:
    if signal_record_id:
        record = await session.get(SignalRecord, signal_record_id)
        if not record or record.user_id != user.id:
            raise ValueError("Signal not found for current user")
    else:
        record = await session.scalar(
            select(SignalRecord)
            .where(SignalRecord.user_id == user.id)
            .order_by(SignalRecord.created_at.desc())
            .limit(1)
        )
        if not record:
            raise ValueError("No signal is available to publish")

    shared = SharedAnalysis(
        user_id=user.id,
        signal_record_id=record.id,
        symbol=record.symbol,
        timeframe=record.timeframe,
        signal=record.signal,
        confidence=record.confidence,
        entry_price=record.entry_price,
        stop_loss=record.stop_loss,
        take_profit=record.take_profit,
        title=title[:180] if title else None,
        note=note[:2000] if note else None,
    )
    session.add(shared)
    await session.commit()
    await session.refresh(shared)
    return shared


async def evaluate_analyst(session: AsyncSession, user_id: int, days: int = 30) -> dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 365)))
    records = (
        await session.scalars(
            select(SignalRecord)
            .where(SignalRecord.user_id == user_id, SignalRecord.created_at >= since)
            .order_by(SignalRecord.created_at.desc())
            .limit(500)
        )
    ).all()

    for record in records:
        if record.status == "pending":
            try:
                await evaluate_record(record)
            except Exception:
                continue
    await session.commit()

    reviewed = [item for item in records if item.status in {"correct", "wrong", "neutral"}]
    correct = sum(1 for item in reviewed if item.status == "correct")
    wrong = sum(1 for item in reviewed if item.status == "wrong")
    neutral = sum(1 for item in reviewed if item.status == "neutral")
    accuracy = round((correct / len(reviewed)) * 100, 2) if reviewed else 0
    avg_outcome = round(
        sum(item.outcome_percent or 0 for item in reviewed) / len(reviewed),
        3,
    ) if reviewed else 0
    followers = await follower_count(session, user_id)
    score = round((accuracy * 0.55) + (min(followers, 1000) / 1000 * 25) + (min(len(reviewed), 100) / 100 * 20), 2)
    return {
        "signals_total": len(records),
        "reviewed": len(reviewed),
        "correct": correct,
        "wrong": wrong,
        "neutral": neutral,
        "accuracy": accuracy,
        "avg_outcome_percent": avg_outcome,
        "followers": followers,
        "score": score,
    }


async def list_top_analysts(session: AsyncSession, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    profiles = (
        await session.scalars(
            select(AnalystProfile)
            .where(AnalystProfile.is_public.is_(True))
            .order_by(AnalystProfile.created_at.desc())
            .limit(50)
        )
    ).all()
    rows = []
    for profile in profiles:
        stats = await evaluate_analyst(session, profile.user_id, days=days)
        rows.append({"profile": profile_to_dict(profile), "stats": stats})
    rows.sort(key=lambda item: item["stats"]["score"], reverse=True)
    return rows[: max(1, min(limit, 25))]


async def followed_analyst_ids(session: AsyncSession, user_id: int) -> set[int]:
    rows = (
        await session.scalars(
            select(AnalystFollow.analyst_user_id).where(AnalystFollow.follower_user_id == user_id)
        )
    ).all()
    return set(rows)


async def list_following(session: AsyncSession, user: User) -> list[dict[str, Any]]:
    follows = (
        await session.scalars(
            select(AnalystFollow)
            .where(AnalystFollow.follower_user_id == user.id)
            .order_by(AnalystFollow.created_at.desc())
        )
    ).all()
    items = []
    for follow in follows:
        profile = await session.scalar(select(AnalystProfile).where(AnalystProfile.user_id == follow.analyst_user_id))
        if profile:
            items.append(
                {
                    "profile": profile_to_dict(profile),
                    "stats": await evaluate_analyst(session, profile.user_id),
                    "followed_at": follow.created_at,
                }
            )
    return items


async def follow_analyst(session: AsyncSession, follower: User, analyst_user_id: int) -> dict[str, Any]:
    if follower.id == analyst_user_id:
        raise ValueError("You cannot follow yourself")
    existing = await session.scalar(
        select(AnalystFollow).where(
            AnalystFollow.follower_user_id == follower.id,
            AnalystFollow.analyst_user_id == analyst_user_id,
        )
    )
    if not existing:
        session.add(AnalystFollow(follower_user_id=follower.id, analyst_user_id=analyst_user_id))
        await session.commit()
    return {"following": True, "analyst_user_id": analyst_user_id}


async def unfollow_analyst(session: AsyncSession, follower: User, analyst_user_id: int) -> dict[str, Any]:
    await session.execute(
        delete(AnalystFollow).where(
            AnalystFollow.follower_user_id == follower.id,
            AnalystFollow.analyst_user_id == analyst_user_id,
        )
    )
    await session.commit()
    return {"following": False, "analyst_user_id": analyst_user_id}


async def upsert_portfolio(
    session: AsyncSession,
    user: User,
    market_type: str,
    capital: float,
    currency: str,
    risk_percent: float,
    max_position_percent: float,
) -> PortfolioSetting:
    setting = await session.scalar(select(PortfolioSetting).where(PortfolioSetting.user_id == user.id))
    if not setting:
        setting = PortfolioSetting(user_id=user.id)
        session.add(setting)
    setting.market_type = market_type[:30]
    setting.capital = max(0, float(capital))
    setting.currency = currency[:12].upper()
    setting.risk_percent = max(0.1, min(float(risk_percent), 10))
    setting.max_position_percent = max(1, min(float(max_position_percent), 100))
    await session.commit()
    await session.refresh(setting)
    return setting


async def get_portfolio(session: AsyncSession, user: User) -> PortfolioSetting:
    setting = await session.scalar(select(PortfolioSetting).where(PortfolioSetting.user_id == user.id))
    if setting:
        return setting
    return await upsert_portfolio(session, user, "crypto", 1000, "USDT", 1, 20)


def position_sizing(signal: dict[str, Any], portfolio: PortfolioSetting, consensus: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = float(signal.get("price") or signal.get("entry_price") or 0)
    levels = signal.get("levels") or {}
    stop = float(levels.get("stop_loss") or signal.get("stop_loss") or 0)
    action = signal.get("signal")
    if action in {"WAIT", "NO_DATA"} or not entry or not stop:
        return {
            "action": "WAIT",
            "reason_fa": "برای پیشنهاد ورود، سیگنال قطعی و حد ضرر معتبر لازم است.",
        }

    risk_amount = portfolio.capital * (portfolio.risk_percent / 100)
    risk_per_unit = abs(entry - stop)
    raw_units = risk_amount / risk_per_unit if risk_per_unit else 0
    raw_value = raw_units * entry
    max_value = portfolio.capital * (portfolio.max_position_percent / 100)
    position_value = min(raw_value, max_value)
    units = position_value / entry if entry else 0
    consensus_bonus = 1.0
    if consensus and consensus.get("majority_signal") == action:
        consensus_bonus = 1.15 if consensus.get("top_analyst_count", 0) >= 3 else 1.05
    position_value = min(position_value * consensus_bonus, max_value)
    units = position_value / entry if entry else 0
    return {
        "action": action,
        "capital": portfolio.capital,
        "currency": portfolio.currency,
        "risk_percent": portfolio.risk_percent,
        "risk_amount": round(risk_amount, 2),
        "entry_price": entry,
        "stop_loss": stop,
        "position_value": round(position_value, 2),
        "units": round(units, 8),
        "max_position_percent": portfolio.max_position_percent,
        "reason_fa": "حجم ورود بر اساس سرمایه، فاصله تا حد ضرر و اجماع تحلیل‌گران محاسبه شد.",
    }


async def analyst_consensus(
    session: AsyncSession,
    symbol: str,
    timeframe: str | None = None,
    days: int = 7,
) -> dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 90)))
    stmt = select(SharedAnalysis).where(
        SharedAnalysis.symbol == symbol.upper(),
        SharedAnalysis.created_at >= since,
    )
    if timeframe:
        stmt = stmt.where(SharedAnalysis.timeframe == timeframe)
    shared = (await session.scalars(stmt.order_by(SharedAnalysis.created_at.desc()).limit(200))).all()
    counts = {"LONG": 0, "SHORT": 0, "WAIT": 0, "NO_DATA": 0}
    for item in shared:
        counts[item.signal] = counts.get(item.signal, 0) + 1
    majority = max(counts, key=counts.get) if shared else "NO_DATA"
    top = await list_top_analysts(session, days=30, limit=10)
    top_user_ids = {item["profile"]["user_id"] for item in top}
    top_items = [item for item in shared if item.user_id in top_user_ids]
    top_counts = {"LONG": 0, "SHORT": 0, "WAIT": 0, "NO_DATA": 0}
    for item in top_items:
        top_counts[item.signal] = top_counts.get(item.signal, 0) + 1
    top_majority = max(top_counts, key=top_counts.get) if top_items else majority
    return {
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "days": days,
        "total_public_analyses": len(shared),
        "counts": counts,
        "majority_signal": majority,
        "top_analyst_count": len(top_items),
        "top_analyst_counts": top_counts,
        "top_analyst_majority": top_majority,
        "summary_fa": f"در بین تحلیل‌های منتشرشده، نظر غالب روی {majority} است. بین تحلیل‌گران برتر نظر غالب {top_majority} است.",
    }


def profile_to_dict(profile: AnalystProfile) -> dict[str, Any]:
    return {
        "user_id": profile.user_id,
        "public_id": profile.public_id,
        "display_name": profile.display_name,
        "bio": profile.bio,
        "market_focus": profile.market_focus,
        "is_public": profile.is_public,
        "created_at": profile.created_at,
    }


def shared_to_dict(shared: SharedAnalysis) -> dict[str, Any]:
    return {
        "id": shared.id,
        "user_id": shared.user_id,
        "signal_record_id": shared.signal_record_id,
        "symbol": shared.symbol,
        "timeframe": shared.timeframe,
        "signal": shared.signal,
        "confidence": shared.confidence,
        "entry_price": shared.entry_price,
        "stop_loss": shared.stop_loss,
        "take_profit": shared.take_profit,
        "title": shared.title,
        "note": shared.note,
        "status": shared.status,
        "created_at": shared.created_at,
    }
