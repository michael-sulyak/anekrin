import asyncio
import json
import logging
import signal
import typing

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


log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging_level = logging.INFO
logging.basicConfig(level=logging_level, format=log_format)

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


shutdown_task = None


async def main() -> typing.NoReturn:
    loop = asyncio.get_running_loop()

    def initiate_shutdown() -> None:
        global shutdown_task
        if shutdown_task is None:
            shutdown_task = loop.create_task(shutdown())

    # Registering the signal handlers
    for signal_name in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signal_name), initiate_shutdown)

    logging.info('Initialization matplotlib...')
    init_settings_for_plt()

    logging.info('Initialization DB...')
    await init_db()

    logging.info('Connecting to MQ...')
    connection = await aio_pika.connect_robust(
        url=config.TELEHOOKS_MQ_URL,
        loop=loop,
    )

    logging.info('Initialization Telegram Bot...')
    telegram_bot = init_telegram_bot()

    handler = TelegramMessageHandler(telegram_bot=telegram_bot)

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
            except asyncio.CancelledError:
                logging.info('Message processing cancelled due to shutdown.')
            except Exception:
                logging.exception('Unexpected error while processing messages')
            finally:
                logging.info('Closing queue iterator...')
                await queue_iter.close()  # Explicitly close the queue iterator
                logging.info('Queue iterator closed.')


async def shutdown() -> None:
    logging.info('Shutdown initialized...')

    current_task = asyncio.current_task()
    tasks = []

    for task in asyncio.all_tasks():
        if task is current_task:
            continue

        task.cancel('Shutdown')
        tasks.append(task)

    # Wait for all tasks to finish
    await asyncio.gather(*tasks, return_exceptions=True)

    # Close the database connection
    await close_db()

    logging.info('Shutdown completed.')

    # Stop the event loop
    asyncio.get_running_loop().stop()


if __name__ == '__main__':
    asyncio.run(main())
