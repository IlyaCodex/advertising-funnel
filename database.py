# -*- coding: utf-8 -*-
import asyncpg
from config import DATABASE_URL

pool: asyncpg.Pool = None


async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)

    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                trial_activated BOOLEAN DEFAULT FALSE,
                referrer_id BIGINT DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        await conn.execute("""
            INSERT INTO settings (key, value) VALUES ('redirect_mode', '0')
            ON CONFLICT (key) DO NOTHING
        """)


async def close_db():
    global pool
    if pool:
        await pool.close()


async def get_setting(key: str) -> str:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT value FROM settings WHERE key = $1", key)
        return row["value"] if row else None


async def set_setting(key: str, value: str):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO settings (key, value) VALUES ($1, $2)
            ON CONFLICT (key) DO UPDATE SET value = $2
        """, key, value)


async def add_user(user_id: int, username: str, first_name: str, referrer_id: int = 0):
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, first_name, referrer_id)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (user_id) DO NOTHING
        """, user_id, username, first_name, referrer_id)


async def is_trial_activated(user_id: int) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT trial_activated FROM users WHERE user_id = $1", user_id
        )
        return row["trial_activated"] if row else False


async def activate_trial(user_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET trial_activated = TRUE WHERE user_id = $1", user_id
        )


async def get_referral_count(user_id: int) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT COUNT(*) as cnt FROM users WHERE referrer_id = $1", user_id
        )
        return row["cnt"] if row else 0


async def get_user_count() -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT COUNT(*) as cnt FROM users")
        return row["cnt"] if row else 0