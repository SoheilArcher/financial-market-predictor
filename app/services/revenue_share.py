from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.revenue import RevenueContributor, RevenuePayout, RevenuePool, RevenueShareRule
from app.models.signal import SignalRecord
from app.models.social import AnalystFollow, SharedAnalysis
from app.models.user import User
from app.services.social_trading import evaluate_analyst


def money(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


async def get_or_create_rule(session: AsyncSession) -> RevenueShareRule:
    rule = await session.scalar(
        select(RevenueShareRule)
        .where(RevenueShareRule.status == "active")
        .order_by(RevenueShareRule.id.desc())
        .limit(1)
    )
    if rule:
        return rule
    rule = RevenueShareRule(owner_percent=Decimal("50"), contributor_percent=Decimal("50"), currency="USD")
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def save_rule(
    session: AsyncSession,
    owner_percent: float,
    contributor_percent: float,
    currency: str = "USD",
    name: str = "Default revenue split",
) -> RevenueShareRule:
    total = Decimal(str(owner_percent)) + Decimal(str(contributor_percent))
    if total != Decimal("100"):
        raise ValueError("Owner percent and contributor percent must equal 100")
    await session.execute(update(RevenueShareRule).where(RevenueShareRule.status == "active").values(status="inactive"))
    rule = RevenueShareRule(
        name=name[:120],
        owner_percent=Decimal(str(owner_percent)),
        contributor_percent=Decimal(str(contributor_percent)),
        currency=currency[:12].upper(),
        status="active",
    )
    session.add(rule)
    await session.commit()
    await session.refresh(rule)
    return rule


async def upsert_contributor(
    session: AsyncSession,
    user_id: int,
    manual_weight: float = 1,
    role_label: str | None = None,
    payout_method: str | None = None,
    payout_account: str | None = None,
    note: str | None = None,
    status: str = "active",
) -> RevenueContributor:
    user = await session.get(User, user_id)
    if not user:
        raise ValueError("User not found")
    contributor = await session.scalar(select(RevenueContributor).where(RevenueContributor.user_id == user_id))
    if not contributor:
        contributor = RevenueContributor(user_id=user_id)
        session.add(contributor)
    contributor.manual_weight = Decimal(str(max(0, manual_weight)))
    contributor.role_label = role_label[:80] if role_label else None
    contributor.payout_method = payout_method[:80] if payout_method else None
    contributor.payout_account = payout_account
    contributor.note = note
    contributor.status = status
    await session.commit()
    await session.refresh(contributor)
    return contributor


async def contributor_activity_score(session: AsyncSession, contributor: RevenueContributor, days: int = 30) -> dict[str, Any]:
    since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 365)))
    user_id = contributor.user_id
    followers = int(
        await session.scalar(select(func.count(AnalystFollow.id)).where(AnalystFollow.analyst_user_id == user_id))
        or 0
    )
    public_analyses = int(
        await session.scalar(
            select(func.count(SharedAnalysis.id)).where(
                SharedAnalysis.user_id == user_id,
                SharedAnalysis.created_at >= since,
            )
        )
        or 0
    )
    signals = int(
        await session.scalar(
            select(func.count(SignalRecord.id)).where(
                SignalRecord.user_id == user_id,
                SignalRecord.created_at >= since,
            )
        )
        or 0
    )
    stats = await evaluate_analyst(session, user_id=user_id, days=days)
    accuracy = Decimal(str(stats["accuracy"]))
    manual = Decimal(contributor.manual_weight or 0)
    score = (
        manual * Decimal("25")
        + Decimal(min(followers, 1000)) * Decimal("0.05")
        + Decimal(min(public_analyses, 100)) * Decimal("0.35")
        + Decimal(min(signals, 300)) * Decimal("0.08")
        + accuracy * Decimal("0.45")
    )
    return {
        "score": float(score.quantize(Decimal("0.0001"))),
        "manual_weight": float(manual),
        "followers": followers,
        "public_analyses": public_analyses,
        "signals": signals,
        "accuracy": float(accuracy),
        "analyst_score": stats["score"],
    }


async def list_contributors(session: AsyncSession) -> list[dict[str, Any]]:
    contributors = (await session.scalars(select(RevenueContributor).order_by(RevenueContributor.id))).all()
    rows = []
    for contributor in contributors:
        user = await session.get(User, contributor.user_id)
        score = await contributor_activity_score(session, contributor)
        rows.append(
            {
                "id": contributor.id,
                "user_id": contributor.user_id,
                "email": user.email if user else None,
                "full_name": user.full_name if user else None,
                "status": contributor.status,
                "manual_weight": float(contributor.manual_weight),
                "role_label": contributor.role_label,
                "payout_method": contributor.payout_method,
                "payout_account": contributor.payout_account,
                "note": contributor.note,
                "score": score,
            }
        )
    return rows


async def create_pool(
    session: AsyncSession,
    period: str,
    gross_revenue: float,
    system_costs: float,
    note: str | None = None,
) -> RevenuePool:
    rule = await get_or_create_rule(session)
    gross = money(gross_revenue)
    costs = money(system_costs)
    net = money(max(Decimal("0"), gross - costs))
    pool = RevenuePool(
        period=period[:20],
        gross_revenue=gross,
        system_costs=costs,
        net_revenue=net,
        currency=rule.currency,
        owner_percent=rule.owner_percent,
        contributor_percent=rule.contributor_percent,
        status="draft",
        note=note,
    )
    session.add(pool)
    await session.commit()
    await session.refresh(pool)
    await recalculate_pool(session, pool.id)
    refreshed = await session.get(RevenuePool, pool.id)
    return refreshed


async def recalculate_pool(session: AsyncSession, pool_id: int) -> dict[str, Any]:
    pool = await session.get(RevenuePool, pool_id)
    if not pool:
        raise ValueError("Revenue pool not found")
    existing = (await session.scalars(select(RevenuePayout).where(RevenuePayout.pool_id == pool_id))).all()
    for payout in existing:
        await session.delete(payout)
    await session.flush()

    owner_amount = money(Decimal(pool.net_revenue) * Decimal(pool.owner_percent) / Decimal("100"))
    contributor_amount = money(Decimal(pool.net_revenue) * Decimal(pool.contributor_percent) / Decimal("100"))
    session.add(
        RevenuePayout(
            pool_id=pool.id,
            user_id=None,
            payout_type="owner",
            amount=owner_amount,
            currency=pool.currency,
            score=Decimal("0"),
            reason_json=json.dumps({"owner_percent": float(pool.owner_percent)}, ensure_ascii=False),
        )
    )
    contributors = (
        await session.scalars(select(RevenueContributor).where(RevenueContributor.status == "active").order_by(RevenueContributor.id))
    ).all()
    scores = []
    for contributor in contributors:
        score_payload = await contributor_activity_score(session, contributor)
        scores.append((contributor, Decimal(str(score_payload["score"])), score_payload))
    score_total = sum((item[1] for item in scores), Decimal("0"))
    for contributor, score, score_payload in scores:
        share = Decimal("0") if score_total == 0 else score / score_total
        amount = money(contributor_amount * share)
        session.add(
            RevenuePayout(
                pool_id=pool.id,
                user_id=contributor.user_id,
                payout_type="contributor",
                amount=amount,
                currency=pool.currency,
                score=score,
                reason_json=json.dumps(score_payload, ensure_ascii=False),
            )
        )
    pool.status = "calculated"
    await session.commit()
    return await pool_summary(session, pool.id)


async def pool_summary(session: AsyncSession, pool_id: int) -> dict[str, Any]:
    pool = await session.get(RevenuePool, pool_id)
    if not pool:
        raise ValueError("Revenue pool not found")
    payouts = (await session.scalars(select(RevenuePayout).where(RevenuePayout.pool_id == pool.id).order_by(RevenuePayout.amount.desc()))).all()
    rows = []
    for payout in payouts:
        user = await session.get(User, payout.user_id) if payout.user_id else None
        rows.append(
            {
                "id": payout.id,
                "user_id": payout.user_id,
                "email": user.email if user else "owner",
                "full_name": user.full_name if user else "Platform Owner",
                "payout_type": payout.payout_type,
                "amount": float(payout.amount),
                "currency": payout.currency,
                "score": float(payout.score),
                "status": payout.status,
                "reason": json.loads(payout.reason_json or "{}"),
                "paid_at": payout.paid_at,
            }
        )
    return {
        "pool": pool_to_dict(pool),
        "payouts": rows,
    }


async def list_pools(session: AsyncSession) -> list[dict[str, Any]]:
    pools = (await session.scalars(select(RevenuePool).order_by(RevenuePool.created_at.desc()).limit(50))).all()
    return [pool_to_dict(pool) for pool in pools]


async def mark_payout_paid(session: AsyncSession, payout_id: int) -> dict[str, Any]:
    payout = await session.get(RevenuePayout, payout_id)
    if not payout:
        raise ValueError("Payout not found")
    payout.status = "paid"
    payout.paid_at = datetime.now(timezone.utc)
    await session.commit()
    return {"id": payout.id, "status": payout.status, "paid_at": payout.paid_at}


def pool_to_dict(pool: RevenuePool) -> dict[str, Any]:
    return {
        "id": pool.id,
        "period": pool.period,
        "gross_revenue": float(pool.gross_revenue),
        "system_costs": float(pool.system_costs),
        "net_revenue": float(pool.net_revenue),
        "currency": pool.currency,
        "owner_percent": float(pool.owner_percent),
        "contributor_percent": float(pool.contributor_percent),
        "status": pool.status,
        "note": pool.note,
        "created_at": pool.created_at,
    }
