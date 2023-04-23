import datetime
import typing
import zoneinfo

from aiogram.types import (
    User as TelegramUser,
)

from ..exceptions import ValidationError
from ... import models


class UserManager:
    user: models.User

    def __init__(self, *, user: models.User) -> None:
        self.user = user

    @classmethod
    async def get_user_by_telegram_user(cls, telegram_user: TelegramUser) -> tuple[models.User, bool]:
        if telegram_user.is_bot:
            raise ValidationError('It\'s the bot')

        user, created = await models.User.get_or_create(
            telegram_user_id=telegram_user.id,
        )

        return user, created

    async def wait_answer_for(self, question_type: str) -> None:
        self.user.wait_answer_for = question_type
        await self.user.save(update_fields=('wait_answer_for',))

    async def clear_waiting_of_answer(self) -> None:
        if self.user.wait_answer_for is None:
            return

        self.user.wait_answer_for = None
        await self.user.save(update_fields=('wait_answer_for',))

    async def update_user_timezone(self, timezone: str) -> None:
        if timezone not in zoneinfo.available_timezones():
            raise ValidationError('Time zone is invalid.')

        self.user.timezone = timezone
        await self.user.save(update_fields=('timezone',))

    async def set_work_date(self, work_date: typing.Optional[datetime.date]) -> None:
        self.user.selected_work_date = work_date
        await self.user.save(update_fields=('selected_work_date',))
