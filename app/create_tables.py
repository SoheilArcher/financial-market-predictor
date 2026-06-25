import asyncio

from app.database import Base, engine
from app.migrations import run_lightweight_migrations
from app.models.comment import Comment
from app.models.market import Exchange, Symbol, Candle
from app.models.revenue import RevenueContributor, RevenuePayout, RevenuePool, RevenueShareRule
from app.models.signal import SignalRecord
from app.models.social import AnalystFollow, AnalystProfile, PortfolioSetting, SharedAnalysis
from app.models.subscription import Plan, Subscription
from app.models.usage import AnalysisUsage
from app.models.user import User


async def seed_default_plans():
    from sqlalchemy import select

    from app.database import AsyncSessionLocal

    defaults = [
        {
            "code": "free",
            "name": "Free",
            "price": 0,
            "currency": "USD",
            "interval_days": 30,
            "max_analyses_per_day": 10,
            "allowed_timeframes": ["5m", "15m"],
            "status": "active",
        },
        {
            "code": "pro",
            "name": "Pro",
            "price": 19,
            "currency": "USD",
            "interval_days": 30,
            "max_analyses_per_day": 200,
            "allowed_timeframes": ["1m", "5m", "15m", "1h", "4h"],
            "status": "active",
        },
        {
            "code": "vip",
            "name": "VIP",
            "price": 49,
            "currency": "USD",
            "interval_days": 30,
            "max_analyses_per_day": 1000,
            "allowed_timeframes": ["1m", "5m", "15m", "1h", "4h", "1d"],
            "status": "active",
        },
    ]

    async with AsyncSessionLocal() as session:
        for item in defaults:
            existing_plan = await session.scalar(select(Plan).where(Plan.code == item["code"]))
            if existing_plan is None:
                session.add(Plan(**item))
        await session.commit()


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await run_lightweight_migrations()
    await seed_default_plans()
    print("Tables created successfully")


if __name__ == "__main__":
    asyncio.run(main())
