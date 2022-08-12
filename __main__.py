import asyncio
import json
import logging
import signal
import typing
from asyncio import exceptions as asyncio_exceptions
from functools import partial

import aio_pika
import aio_pika.abc
import matplotlib
import pandas as pd
import sentry_sdk
from aiogram.types import Update as TelegramUpdate
from matplotlib import pyplot as plt
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration

from app import config
from app.core.services.telegram import TelegramMessageHandler
from app.core.utils import init_telegram_bot
from app.models.utils import close_db, init_db


logging_level = logging.INFO
logging.basicConfig(level=logging_level)

sentry_sdk.init(
    dsn=config.SENTRY_DSN,
    integrations=(
        LoggingIntegration(
            level=logging_level,
            event_level=logging.ERROR,
        ),
        ThreadingIntegration(
            propagate_hub=True,
        ),
    ),
)


def init_settings_for_plt() -> None:
    import mplcyberpunk  # NOQA

    matplotlib.use('Agg')
    plt.ioff()
    pd.plotting.register_matplotlib_converters()
    plt.rcParams.update({'font.family': 'Roboto'})

    plt.style.use('cyberpunk')


async def main() -> typing.NoReturn:
    logging.info('Initialization Telegram Bot...')
    init_telegram_bot()

    logging.info('Initialization matplotlib...')
    init_settings_for_plt()

    logging.info('Initialization DB...')
    await init_db()

    logging.info('Connecting to MQ...')
    connection = await aio_pika.connect_robust(
        url=config.TELEHOOKS_MQ_URL,
        loop=asyncio.get_running_loop(),
    )
    handler = TelegramMessageHandler()

    async with connection:
        channel: aio_pika.abc.AbstractChannel = await connection.channel()
        queue: aio_pika.abc.AbstractQueue = await channel.declare_queue(config.TELEHOOKS_MQ_QUEUE_NAME)

        async with queue.iterator() as queue_iter:
            message: aio_pika.abc.AbstractIncomingMessage

            logging.info('Ready to handle messages.')

            try:
                async for message in queue_iter:
                    async with message.process():
                        telegram_update = TelegramUpdate(**json.loads(message.body))
                        await handler.process_update(telegram_update)
            except (asyncio_exceptions.CancelledError, asyncio_exceptions.TimeoutError,):
                pass


async def shutdown() -> None:
    logging.info('Shutdown initialized...')

    current_task = asyncio.current_task()
    tasks = []

    for task in asyncio.all_tasks():
        if task is current_task:
            continue

        task.cancel('Shutdown')
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)
    await close_db()

    logging.info('Shutdown completed.')

    asyncio.get_running_loop().stop()


if __name__ == '__main__':
    main_loop = asyncio.new_event_loop()

    for signal_name in ('SIGINT', 'SIGTERM',):
        main_loop.add_signal_handler(getattr(signal, signal_name), partial(main_loop.create_task, shutdown()))

    main_loop.create_task(main())

    try:
        main_loop.run_forever()
    finally:
        main_loop.close()
        logging.info('Successfully shutdown service.')
