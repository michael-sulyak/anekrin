import asyncio
import typing

import pytest
from tortoise import Tortoise

from ... import config
from ...models.utils import close_db, get_common_db_connection, init_db


__all__ = (
    'event_loop',
    'setup_database',
    'clean_db',
)


@pytest.fixture(scope='session')
def event_loop() -> typing.Generator:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()

    yield loop

    loop.close()


@pytest.fixture(scope='session', autouse=True)
async def setup_database() -> typing.Generator:
    assert config.DATABASE_NAME.endswith('_test')

    common_conn = await get_common_db_connection()
    await common_conn.execute(f'DROP DATABASE IF EXISTS {config.DATABASE_NAME};')
    await common_conn.execute(f'CREATE DATABASE {config.DATABASE_NAME};')
    await common_conn.close()

    await init_db(generate_schema=True)

    yield

    await close_db()

    common_conn = await get_common_db_connection()
    await common_conn.execute(f'DROP DATABASE {config.DATABASE_NAME};')
    await common_conn.close()


@pytest.fixture(autouse=True)
async def clean_db() -> None:
    conn = Tortoise.get_connection('default')

    if not hasattr(clean_db, 'sql_for_truncate'):
        count, results = await conn.execute_query("""
            SELECT table_name
            FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE';
        """)

        table_names = tuple(
            f'"{result["table_name"]}"'
            for result in results
        )

        if table_names:
            clean_db.sql_for_truncate = f'TRUNCATE {", ".join(table_names)};'
        else:
            clean_db.sql_for_truncate = None

    if clean_db.sql_for_truncate:
        await conn.execute_query(clean_db.sql_for_truncate)
