import contextlib
import typing

import asyncpg
from asyncpg import Connection
from tortoise import Tortoise, transactions
from tortoise.queryset import ValuesListQuery, ValuesQuery

from . import config
from .. import models
from ..core import constants


@contextlib.asynccontextmanager
async def lock_by_user(user_id: int) -> typing.AsyncContextManager:
    async with transactions.in_transaction():
        await models.User.filter(id=user_id).select_for_update()
        yield


async def create_task(*,
                      name: str,
                      reward: int,
                      owner: models.User) -> models.Task:
    async with lock_by_user(owner.id):
        max_position = await get_first(models.Task.filter(
            owner=owner,
        ).order_by(
            '-position',
        ).values_list(
            'position',
            flat=True,
        ))

        if max_position is None:
            max_position = 0

        return await models.Task.create(
            name=name,
            owner=owner,
            position=max_position + 1,
            reward=reward,
        )


async def create_work_log(*, task: models.Task, type_: str = constants.WorkLogTypes.USER_WORK) -> models.WorkLog:
    return await models.WorkLog.create(
        task=task,
        type=type_,
        name=task.name,
        owner=task.owner,
        date=task.owner.get_selected_work_date(),
        reward=task.reward,
    )


async def get_first(query: ValuesListQuery) -> typing.Any:
    query.limit = 1
    result = await query

    if not result:
        return None

    return result[0]


async def get_count(query: typing.Union[ValuesListQuery, ValuesQuery]) -> int:
    conn = Tortoise.get_connection('default')
    return (await conn.execute_query(f'SELECT COUNT(*) FROM ({query.as_query()}) AS temp;'))[0]


async def get_common_db_connection() -> Connection:
    return await asyncpg.connect(
        user=config.DATABASE_USER,
        password=config.DATABASE_PASSWORD,
        host=config.DATABASE_HOST,
        port=config.DATABASE_PORT,
        database='template1',
    )


async def init_db(*, generate_schema: bool = False) -> None:
    await Tortoise.init(config=config.TORTOISE_ORM)

    # for connection in Tortoise._connections.values():
    #     schema = get_schema_sql(connection, safe=True)
    #     print(schema)

    if generate_schema:
        await Tortoise.generate_schemas(safe=True)


async def close_db() -> None:
    await Tortoise.close_connections()
