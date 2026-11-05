import os
from typing import Optional

from psycopg import AsyncConnection
from psycopg_pool import AsyncConnectionPool


pool: Optional[AsyncConnectionPool] = None


def get_database_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")
    return db_url


def get_pool() -> AsyncConnectionPool:
    global pool
    if pool is None:
        pool = AsyncConnectionPool(get_database_url(), open=False)
    return pool


async def init_pool() -> None:
    pool = get_pool()
    await pool.open()


async def close_pool() -> None:
    global pool
    if pool is not None:
        await pool.close()
        pool = None


async def ensure_threads_table() -> None:
    pool = get_pool()
    async with pool.connection() as conn:  # type: AsyncConnection
        async with conn.cursor() as cur:
            await cur.execute(
                """
                create table if not exists threads (
                    thread_id text primary key,
                    created_at timestamptz not null default now()
                );
                """
            )
            await conn.commit()


async def insert_thread(thread_id: str) -> None:
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                insert into threads (thread_id)
                values (%s)
                on conflict (thread_id) do nothing
                """,
                (thread_id,),
            )
            await conn.commit()


async def get_thread_created_at(thread_id: str) -> Optional[str]:
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                select to_char(created_at at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
                  from threads
                 where thread_id = %s
                """,
                (thread_id,),
            )
            row = await cur.fetchone()
            return row[0] if row else None


async def list_threads(limit: int = 50) -> list[tuple[str, str]]:
    pool = get_pool()
    async with pool.connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """
                select thread_id,
                       to_char(created_at at time zone 'utc', 'YYYY-MM-DD"T"HH24:MI:SS"Z"') as created
                  from threads
                 order by created_at desc
                 limit %s
                """,
                (limit,),
            )
            rows = await cur.fetchall()
            return [(r[0], r[1]) for r in rows]
