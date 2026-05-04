import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings

logger = logging.getLogger(__name__)

# Async SQLAlchemy engine for Railway PostgreSQL
engine = create_async_engine(
    settings.async_db_url,
    echo=settings.is_dev,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for use outside of FastAPI request scope (e.g. background tasks)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Verify DB connection and auto-apply pending schema migrations on startup."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("[DB] Connection OK — Railway PostgreSQL")
    except Exception as exc:
        logger.error(f"[DB] Connection FAILED: {exc}")
        raise

    # ── Auto-migrations (idempotent — safe to run on every startup) ───────────
    _MIGRATIONS = [
        # 002: process_log column for pipeline transparency diagram
        "ALTER TABLE valuations ADD COLUMN IF NOT EXISTS process_log JSONB NOT NULL DEFAULT '{}'",
        # 003: convert TEXT[] → JSONB for SWOT arrays so ORM (JSONB) matches DB
        """DO $$ BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'valuations'
                  AND column_name = 'strengths'
                  AND data_type = 'ARRAY'
            ) THEN
                ALTER TABLE valuations
                    ALTER COLUMN strengths      TYPE JSONB USING to_json(strengths)::jsonb,
                    ALTER COLUMN weaknesses     TYPE JSONB USING to_json(weaknesses)::jsonb,
                    ALTER COLUMN opportunities  TYPE JSONB USING to_json(opportunities)::jsonb,
                    ALTER COLUMN threats        TYPE JSONB USING to_json(threats)::jsonb,
                    ALTER COLUMN recommendations TYPE JSONB USING to_json(recommendations)::jsonb;
            END IF;
        END $$""",
    ]
    for stmt in _MIGRATIONS:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(stmt))
            logger.info(f"[DB] migration OK: {stmt[:70].strip()}…")
        except Exception as mig_exc:
            logger.warning(f"[DB] migration skipped (likely already applied): {mig_exc}")
