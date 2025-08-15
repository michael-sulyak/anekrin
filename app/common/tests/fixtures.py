import asyncio
import typing

import asyncpg
import pytest_asyncio

from ... import config
from ...models.utils import close_db, get_common_db_connection, init_db


__all__ = (
    'event_loop',
    'setup_database',
    'clean_db',
)


@pytest_asyncio.fixture(scope='session')
def event_loop() -> typing.Generator:
    loop = asyncio.new_event_loop()
    try:
        yield loop
    finally:
        loop.close()


async def _get_app_db_connection() -> asyncpg.Connection:
    return await asyncpg.connect(
        user=config.DATABASE_USER,
        password=config.DATABASE_PASSWORD,
        host=config.DATABASE_HOST,
        port=config.DATABASE_PORT,
        database=config.DATABASE_NAME,
    )


@pytest_asyncio.fixture(scope='session', autouse=True)
async def setup_database() -> typing.AsyncGenerator[None, None]:
    assert config.DATABASE_NAME.endswith('_test')

    # Create/drop DB using template1 (or postgres)
    common_conn = await get_common_db_connection()
    await common_conn.execute(f'DROP DATABASE IF EXISTS {config.DATABASE_NAME};')
    await common_conn.execute(f'CREATE DATABASE {config.DATABASE_NAME};')
    await common_conn.close()

    # Initialize ORM and schema once
    await init_db(generate_schema=True)

    yield

    # Close ORM connections
    await close_db()

    # Drop test DB
    common_conn = await get_common_db_connection()
    await common_conn.execute(f'DROP DATABASE {config.DATABASE_NAME};')
    await common_conn.close()


@pytest_asyncio.fixture(autouse=True)
async def clean_db() -> None:
    # Compute the TRUNCATE statement once
    if not hasattr(clean_db, 'sql_for_truncate'):
        conn = await _get_app_db_connection()
        try:
            rows = await conn.fetch(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_type = 'BASE TABLE';
                """
            )
            table_names = tuple(f'"{row["table_name"]}"' for row in rows)

            if table_names:
                # Reset sequences and cascade FKs
                clean_db.sql_for_truncate = f'TRUNCATE {", ".join(table_names)} RESTART IDENTITY CASCADE;'
            else:
                clean_db.sql_for_truncate = None
        finally:
            await conn.close()

    if clean_db.sql_for_truncate:
        conn = await _get_app_db_connection()
        try:
            await conn.execute(clean_db.sql_for_truncate)
        finally:
            await conn.close()
