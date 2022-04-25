import abc
import typing

from aiogram.types import (
    InlineKeyboardMarkup, Message as TelegramMessage,
)
from aiogram.utils.exceptions import MessageNotModified

from .constants import ParseModes
from .exceptions import ValidationError
from .services.tasks import TaskManager
from .services.users import UserManager
from .. import models


class BaseMessage(abc.ABC):
    from_user: models.User
    _telegram_message: TelegramMessage

    def __init__(self, *,
                 from_user: models.User,
                 telegram_message: TelegramMessage) -> None:
        self.from_user = from_user
        self._telegram_message = telegram_message

    @abc.abstractmethod
    async def answer(self, *args, **kwargs) -> TelegramMessage:
        pass

    @abc.abstractmethod
    async def answer_error(self, error: ValidationError, **kwargs) -> TelegramMessage:
        pass

    @abc.abstractmethod
    async def answer_document(self, *args, **kwargs) -> TelegramMessage:
        pass

    @abc.abstractmethod
    async def reply(self, *args, **kwargs) -> TelegramMessage:
        pass

    @abc.abstractmethod
    async def edit_reply_markup(self, reply_markup: typing.Optional[InlineKeyboardMarkup] = None) -> None:
        pass


class Message(BaseMessage):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.user_manager = UserManager(user=self.from_user)
        self.task_manager = TaskManager(user=self.from_user)

    async def answer(self, *args, **kwargs) -> TelegramMessage:
        from .utils import get_main_reply_keyboard_markup

        if 'reply_markup' not in kwargs:
            kwargs['reply_markup'] = get_main_reply_keyboard_markup()

        return await self._telegram_message.answer(*args, **kwargs)

    async def answer_error(self, error: ValidationError, **kwargs) -> TelegramMessage:
        return await self.answer(
            error.msg,
            parse_mode=ParseModes.MARKDOWN_V2 if error.is_markdown else ParseModes.TEXT,
            **kwargs,
        )

    async def answer_document(self, *args, **kwargs) -> TelegramMessage:
        from .utils import get_main_reply_keyboard_markup

        if 'reply_markup' not in kwargs:
            kwargs['reply_markup'] = get_main_reply_keyboard_markup()

        return await self._telegram_message.answer_document(*args, **kwargs)

    async def reply(self, *args, **kwargs) -> TelegramMessage:
        from .utils import get_main_reply_keyboard_markup

        if 'reply_markup' not in kwargs:
            kwargs['reply_markup'] = get_main_reply_keyboard_markup()

        return await self._telegram_message.reply(*args, **kwargs)

    async def edit_reply_markup(self, reply_markup: typing.Optional[InlineKeyboardMarkup] = None) -> None:
        if self._telegram_message.reply_markup == reply_markup:
            return

        try:
            await self._telegram_message.edit_reply_markup(reply_markup)
        except MessageNotModified:
            # The top check may not work if a user sent the same request several times.
            pass
