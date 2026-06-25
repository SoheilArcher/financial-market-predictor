from sqlalchemy import text

from app.database import engine


async def run_lightweight_migrations():
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS country VARCHAR(80)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMP WITH TIME ZONE"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_token VARCHAR(128)"))
        await conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verification_sent_at TIMESTAMP WITH TIME ZONE"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_country ON users (country)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_email_verification_token ON users (email_verification_token)"))
        await conn.execute(text("UPDATE users SET email_verified_at = NOW() WHERE status = 'active' AND email_verified_at IS NULL"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analyst_profiles_public_id ON analyst_profiles (public_id)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_shared_analyses_symbol_timeframe ON shared_analyses (symbol, timeframe)"))
