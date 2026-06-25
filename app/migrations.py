from sqlalchemy import text

from app.database import engine


async def run_lightweight_migrations():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS country VARCHAR(80)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_country ON users (country)"))
