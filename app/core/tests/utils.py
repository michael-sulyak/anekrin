import typing

from aiogram.types import (
    Message as TelegramMessage,
)

from ..base import BaseMessage
from ...common.tests.dto import ActualCall


def create_mocked_class_for_message() -> tuple[typing.Type[BaseMessage], list[ActualCall]]:
    calls = []

    class MockedMessage(BaseMessage):
        async def answer(self, *args, **kwargs) -> TelegramMessage:
            calls.append(ActualCall('answer', args, kwargs))
            return TelegramMessage()

        async def answer_document(self, *args, **kwargs) -> TelegramMessage:
            calls.append(ActualCall('answer_document', args, kwargs))
            return TelegramMessage()

        async def reply(self, *args, **kwargs) -> TelegramMessage:
            calls.append(ActualCall('reply', args, kwargs))
            return TelegramMessage()

        async def edit_reply_markup(self, *args, **kwargs) -> None:
            calls.append(ActualCall('edit_reply_markup', args, kwargs))

    return MockedMessage, calls
