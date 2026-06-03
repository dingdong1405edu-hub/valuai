import json
import os
from datetime import datetime
from typing import Optional

import asyncpg

_pool: Optional[asyncpg.Pool] = None


async def init_pool():
    global _pool
    url = os.environ.get("DATABASE_URL")
    if not url:
        return
    _pool = await asyncpg.create_pool(url, min_size=1, max_size=10)
    await _create_tables()


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


async def _create_tables():
    async with _pool.acquire() as conn:
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id                SERIAL PRIMARY KEY,
            job_id            VARCHAR(32) UNIQUE NOT NULL,
            created_at        TIMESTAMPTZ DEFAULT NOW(),
            website_url       TEXT,
            filename          TEXT,
            file_size_bytes   INTEGER,
            company_name      TEXT,
            industry_name     TEXT,
            status            VARCHAR(20) DEFAULT 'processing',
            error_message     TEXT,
            total_elapsed_sec FLOAT,
            ip_address        TEXT,
            session_id        VARCHAR(128),
            result_json       TEXT,
            user_id           INTEGER
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id            SERIAL PRIMARY KEY,
            username      VARCHAR(64) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS end_users (
            id            SERIAL PRIMARY KEY,
            email         VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name  VARCHAR(128),
            created_at    TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS payment_orders (
            id           BIGSERIAL PRIMARY KEY,
            job_id       VARCHAR(32) NOT NULL,
            amount       INTEGER NOT NULL,
            package_type VARCHAR(20) DEFAULT 'basic',
            status       VARCHAR(20) DEFAULT 'pending',
            created_at   TIMESTAMPTZ DEFAULT NOW(),
            paid_at      TIMESTAMPTZ,
            order_code   BIGINT
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS report_configs (
            id          SERIAL PRIMARY KEY,
            config_json TEXT NOT NULL,
            is_active   BOOLEAN DEFAULT FALSE,
            updated_by  TEXT,
            updated_at  TIMESTAMPTZ DEFAULT NOW()
        )
        """)
        await conn.execute("""
        CREATE TABLE IF NOT EXISTS job_config_snapshots (
            job_id      VARCHAR(32) PRIMARY KEY,
            config_json TEXT NOT NULL,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
        """)


# ── Usage logs ──────────────────────────────────────────────────────────────

async def create_job(job_id: str, website_url: str, filename: str,
                     file_size: int, ip: str, session_id: str,
                     user_id: Optional[int] = None):
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO usage_logs
              (job_id, website_url, filename, file_size_bytes,
               ip_address, session_id, user_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            ON CONFLICT (job_id) DO NOTHING
        """, job_id, website_url, filename, file_size, ip, session_id, user_id)


async def update_job_status(job_id: str, status: str,
                             company_name: str = None,
                             industry_name: str = None,
                             error_message: str = None,
                             elapsed_sec: float = None,
                             result_json: str = None):
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute("""
            UPDATE usage_logs SET
              status=$2,
              company_name=COALESCE($3, company_name),
              industry_name=COALESCE($4, industry_name),
              error_message=COALESCE($5, error_message),
              total_elapsed_sec=COALESCE($6, total_elapsed_sec),
              result_json=COALESCE($7, result_json)
            WHERE job_id=$1
        """, job_id, status, company_name, industry_name,
            error_message, elapsed_sec, result_json)


async def get_job(job_id: str) -> Optional[dict]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM usage_logs WHERE job_id=$1", job_id
        )
        return dict(row) if row else None


async def get_stats() -> dict:
    if not _pool:
        return {}
    async with _pool.acquire() as conn:
        total = await conn.fetchval("SELECT COUNT(*) FROM usage_logs")
        success = await conn.fetchval(
            "SELECT COUNT(*) FROM usage_logs WHERE status='success'"
        )
        paid = await conn.fetchval(
            "SELECT COUNT(*) FROM payment_orders WHERE status='paid'"
        )
        return {"total_jobs": total, "successful_jobs": success, "paid_jobs": paid}


async def get_recent_jobs(limit: int = 50) -> list:
    if not _pool:
        return []
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM usage_logs ORDER BY created_at DESC LIMIT $1", limit
        )
        return [dict(r) for r in rows]


async def get_session_history(session_id: str) -> list:
    if not _pool:
        return []
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM usage_logs WHERE session_id=$1 ORDER BY created_at DESC",
            session_id
        )
        return [dict(r) for r in rows]


async def get_user_history(user_id: int) -> list:
    if not _pool:
        return []
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM usage_logs WHERE user_id=$1 ORDER BY created_at DESC",
            user_id
        )
        return [dict(r) for r in rows]


# ── Admin users ──────────────────────────────────────────────────────────────

async def get_admin_by_username(username: str) -> Optional[dict]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM admin_users WHERE username=$1", username
        )
        return dict(row) if row else None


async def create_admin(username: str, password_hash: str):
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES ($1,$2)",
            username, password_hash
        )


async def count_admins() -> int:
    if not _pool:
        return 0
    async with _pool.acquire() as conn:
        return await conn.fetchval("SELECT COUNT(*) FROM admin_users")


async def update_admin_password(username: str, password_hash: str):
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE admin_users SET password_hash=$2 WHERE username=$1",
            username, password_hash
        )


# ── End users ────────────────────────────────────────────────────────────────

async def create_end_user(email: str, password_hash: str,
                           display_name: str = None) -> int:
    if not _pool:
        return -1
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """INSERT INTO end_users (email, password_hash, display_name)
               VALUES ($1,$2,$3) RETURNING id""",
            email, password_hash, display_name
        )
        return row["id"]


async def get_end_user_by_email(email: str) -> Optional[dict]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM end_users WHERE email=$1", email
        )
        return dict(row) if row else None


async def get_end_user_by_id(uid: int) -> Optional[dict]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM end_users WHERE id=$1", uid
        )
        return dict(row) if row else None


# ── Payment orders ────────────────────────────────────────────────────────────

async def create_payment_order(job_id: str, amount: int,
                                package_type: str, order_code: int):
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO payment_orders
               (job_id, amount, package_type, order_code)
               VALUES ($1,$2,$3,$4)""",
            job_id, amount, package_type, order_code
        )


async def mark_order_paid(order_code: int, paid_at: datetime):
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute(
            "UPDATE payment_orders SET status='paid', paid_at=$2 WHERE order_code=$1",
            order_code, paid_at
        )


async def get_payment_order_by_code(order_code: int) -> Optional[dict]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM payment_orders WHERE order_code=$1", order_code
        )
        return dict(row) if row else None


async def get_payment_by_job(job_id: str) -> Optional[dict]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT * FROM payment_orders WHERE job_id=$1 ORDER BY created_at DESC LIMIT 1",
            job_id
        )
        return dict(row) if row else None


async def get_paid_package(job_id: str) -> Optional[str]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT package_type FROM payment_orders WHERE job_id=$1 AND status='paid' LIMIT 1",
            job_id
        )
        return row["package_type"] if row else None


# ── Config ────────────────────────────────────────────────────────────────────

async def save_config(config_json: str, updated_by: str) -> int:
    if not _pool:
        return -1
    async with _pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("UPDATE report_configs SET is_active=FALSE")
            row = await conn.fetchrow(
                """INSERT INTO report_configs (config_json, is_active, updated_by)
                   VALUES ($1, TRUE, $2) RETURNING id""",
                config_json, updated_by
            )
            return row["id"]


async def load_active_config() -> Optional[str]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT config_json FROM report_configs WHERE is_active=TRUE LIMIT 1"
        )
        return row["config_json"] if row else None


async def load_config_version(version_id: int) -> Optional[str]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT config_json FROM report_configs WHERE id=$1", version_id
        )
        return row["config_json"] if row else None


async def list_config_versions() -> list:
    if not _pool:
        return []
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, updated_by, updated_at, is_active FROM report_configs ORDER BY id DESC"
        )
        return [dict(r) for r in rows]


# ── Job config snapshots ──────────────────────────────────────────────────────

async def save_job_config_snapshot(job_id: str, config_json: str):
    if not _pool:
        return
    async with _pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO job_config_snapshots (job_id, config_json)
               VALUES ($1,$2)
               ON CONFLICT (job_id) DO UPDATE SET config_json=$2""",
            job_id, config_json
        )


async def load_job_config_snapshot(job_id: str) -> Optional[str]:
    if not _pool:
        return None
    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT config_json FROM job_config_snapshots WHERE job_id=$1", job_id
        )
        return row["config_json"] if row else None


# ── Export ────────────────────────────────────────────────────────────────────

async def export_usage_csv() -> str:
    if not _pool:
        return "job_id,status,company_name,created_at\n"
    async with _pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM usage_logs ORDER BY created_at DESC"
        )
    lines = ["job_id,status,company_name,industry_name,filename,created_at,elapsed_sec,ip_address"]
    for r in rows:
        lines.append(
            f"{r['job_id']},{r['status']},{r['company_name'] or ''},"
            f"{r['industry_name'] or ''},{r['filename'] or ''},"
            f"{r['created_at']},{r['total_elapsed_sec'] or ''},"
            f"{r['ip_address'] or ''}"
        )
    return "\n".join(lines)
