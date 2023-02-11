import pytest

from ....constants import BotCommand
from ....services.telegram import TelegramMessageHandler
from ....tests.utils import create_mocked_class_for_message
from ..... import models
from .....common.tests.dto import ExpectedCall, ExpectedCalls
from .....common.tests.utils import generate_random_raw_user, generate_telegram_update_for_text


@pytest.mark.asyncio
async def test_start() -> None:
    sender = generate_random_raw_user()
    telegram_update = generate_telegram_update_for_text(
        BotCommand.START,
        sender=sender,
    )

    message_class, calls = create_mocked_class_for_message()
    handler = TelegramMessageHandler(message_class=message_class)

    await handler.process_update(telegram_update, immediately=True)

    ExpectedCalls(
        ExpectedCall(
            name='answer',
            args=('Hello! What have you done usefully today?',),
        ),
        ExpectedCall(
            name='answer',
            args__0__contains='*Anekrin* is an easy\\-to\\-use personal productivity tracker that helps you',
            args__len=1,
        ),
        ExpectedCall(
            name='answer',
            args__0__contains='Don\'t forget to update your time zone in the settings.',
            args__len=1,
        ),
        ExpectedCall(
            name='answer',
            args__0__contains='I created samples for your. You can delete them.',
            args__len=1,
        ),
    ).compare_with(calls)

    assert await models.User.filter(telegram_user_id=sender['id']).exists()
    assert await models.Task.filter(owner__telegram_user_id=sender['id']).count() == 4
