import datetime
import random
import typing

from aiogram.types import (Chat as TelegramChat, Message as TelegramMessage)

from ..base import BaseMessage
from ...common.tests.dto import ActualCall


def create_mocked_class_for_message() -> tuple[typing.Type[BaseMessage], list[ActualCall]]:
    calls = []

    msg = TelegramMessage(
        message_id=random.randint(1, 1_000_000),
        chat=TelegramChat(id=random.randint(1, 1_000_000), type='private'),
        date=int(datetime.datetime.now().timestamp()),
    )

    class MockedMessage(BaseMessage):
        async def answer(self, *args, **kwargs) -> TelegramMessage:
            calls.append(ActualCall('answer', args, kwargs))
            return msg

        async def answer_error(self, *args, **kwargs) -> TelegramMessage:
            calls.append(ActualCall('answer_error', args, kwargs))
            return msg

        async def answer_document(self, *args, **kwargs) -> TelegramMessage:
            calls.append(ActualCall('answer_document', args, kwargs))
            return msg

        async def reply(self, *args, **kwargs) -> TelegramMessage:
            calls.append(ActualCall('reply', args, kwargs))
            return msg

        async def edit_reply_markup(self, *args, **kwargs) -> None:
            calls.append(ActualCall('edit_reply_markup', args, kwargs))

    return MockedMessage, calls
