import pytest

from ....constants import BotCommand
from ....services.telegram import TelegramMessageHandler
from ....tests.utils import create_mocked_class_for_message
from ..... import models
from .....common.tests.dto import ExpectedCall, ExpectedCalls
from .....common.tests.utils import generate_random_raw_user, generate_random_string, generate_telegram_update_for_text
from .....models.utils import create_task


@pytest.mark.asyncio
async def test_show_tasks_without_tasks() -> None:
    sender = generate_random_raw_user()
    await models.User.create(telegram_user_id=sender['id'])
    telegram_update = generate_telegram_update_for_text(
        BotCommand.SHOW_TASKS,
        sender=sender,
    )

    message_class, calls = create_mocked_class_for_message()
    handler = TelegramMessageHandler(message_class=message_class)

    await handler.process_update(telegram_update, immediately=True)

    ExpectedCalls(
        ExpectedCall(
            name='answer',
            args__0__contains='You don\'t have tasks',
            args__len=1,
            kwargs__keys={'reply_markup'},
        ),
    ).compare_with(calls)


@pytest.mark.asyncio
async def test_show_tasks() -> None:
    sender = generate_random_raw_user()
    user = await models.User.create(telegram_user_id=sender['id'])
    task = await create_task(name=generate_random_string(10), reward=20, owner=user)

    telegram_update = generate_telegram_update_for_text(
        BotCommand.SHOW_TASKS,
        sender=sender,
    )
    message_class, calls = create_mocked_class_for_message()
    handler = TelegramMessageHandler(message_class=message_class)

    await handler.process_update(telegram_update, immediately=True)

    ExpectedCalls(
        ExpectedCall(
            name='answer',
            args=('Your current tasks:',),
            kwargs__len=0,
        ),
        ExpectedCall(
            name='answer',
            args__0__contains=task.name,
            args__len=1,
            kwargs__keys={'reply_markup', 'parse_mode'},
        ),
        ExpectedCall(
            name='answer',
            args=('Or do you want to do something else?',),
        ),
    ).compare_with(calls)
