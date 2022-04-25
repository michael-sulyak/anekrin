import datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.markdown import escape_md
from emoji.core import emojize

from ..base import BaseHandler
from ..constants import HandlerTypes
from ...constants import BotCommand, CallbackCommands, ParseModes, QuestionTypes
from ...exceptions import ValidationError
from ...services.users import UserManager
from ...utils import get_btn_for_cancel_question, get_btn_for_reset_work_date, get_reply_for_cancel_question


__all__ = (
    'ShowSettings',
    'ChooseDate',
    'UpdateTZ',
    'AnswerWithTZ',
    'ResetWorkDate',
)


class ShowSettings(BaseHandler):
    name = BotCommand.SHOW_SETTING
    type = HandlerTypes.MESSAGE

    async def handle(self) -> None:
        await self.message.answer('What do you want?', reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        f'{emojize(":calendar:")} Choose date',
                        callback_data=CallbackCommands.CHOOSE_DATE,
                    ),
                    InlineKeyboardButton(
                        f'{emojize(":two-thirty:")} Change time zone',
                        callback_data=CallbackCommands.UPDATE_TIMEZONE,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f'{emojize(":inbox_tray:")} Import work logs',
                        callback_data=CallbackCommands.IMPORT_WORK_LOGS,
                    ),
                    InlineKeyboardButton(
                        f'{emojize(":outbox_tray:")} Export data',
                        callback_data=CallbackCommands.EXPORT_DATA,
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f'{emojize(":carpentry_saw:")} Edit all tasks',
                        callback_data=CallbackCommands.REWRITE_ALL_TASKS,
                    ),
                    InlineKeyboardButton(
                        f'{emojize(":information:")} Help',
                        callback_data=CallbackCommands.HELP,
                    ),
                ]
            ],
        ))


class ChooseDate(BaseHandler):
    name = CallbackCommands.CHOOSE_DATE
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        user_manager = UserManager(user=self.message.from_user)
        current_date = datetime.date.today().isoformat()

        await user_manager.wait_answer_for(QuestionTypes.SET_WORK_DATE)

        await self.message.answer(
            (
                f'Enter a date to edit the data \\(for example, `{current_date}`\\)\\.\n'
                f'{emojize(":warning:")} Don\'t forget to reset the date after data editing\\.'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [get_btn_for_reset_work_date()],
                    [get_btn_for_cancel_question('Cancel date selection')],
                ],
            ),
        )


class UpdateTZ(BaseHandler):
    name = CallbackCommands.UPDATE_TIMEZONE
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        user_manager = UserManager(user=self.message.from_user)
        await user_manager.wait_answer_for(QuestionTypes.UPDATE_TIMEZONE)

        link_with_tz = escape_md('https://en.wikipedia.org/wiki/List_of_tz_database_time_zones')

        await self.message.answer(
            (
                f'*Your time zone:* `{escape_md(self.message.from_user.timezone)}`\n\n'
                f'*Available time zones:*\n'
                f'[{link_with_tz}]({link_with_tz})\n'
                f'\\(Look column *"TZ database name"*\\)\n\n'
                f'After choosing, send a time zone to this chat\\.'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
            reply_markup=get_reply_for_cancel_question('Cancel time zone selecting'),
        )


class AnswerWithTZ(BaseHandler):
    name = QuestionTypes.UPDATE_TIMEZONE
    type = HandlerTypes.ANSWER

    async def handle(self, *args) -> None:
        [new_timezone] = args
        user_manager = UserManager(user=self.message.from_user)

        try:
            await user_manager.update_user_timezone(new_timezone)
        except ValidationError as e:
            await self.message.answer_error(
                e,
                reply_markup=get_reply_for_cancel_question('Cancel time zone selecting'),
            )
            return

        await user_manager.clear_waiting_of_answer()

        await self.message.reply(
            f'Successfully saved {emojize(":thumbs_up:")}',
        )


class SetWorkDate(BaseHandler):
    name = QuestionTypes.SET_WORK_DATE
    type = HandlerTypes.ANSWER

    async def handle(self, *args) -> None:
        [new_work_date] = args
        user_manager = UserManager(user=self.message.from_user)

        reply_markup_for_waiting_of_answer = InlineKeyboardMarkup(
            inline_keyboard=[
                [get_btn_for_reset_work_date()],
                [get_btn_for_cancel_question('Cancel date selection')],
            ],
        )

        try:
            new_work_date = datetime.date.fromisoformat(new_work_date)
        except ValueError:
            await self.message.reply(
                f'`{escape_md(new_work_date)}` is invalid date\\.\n'
                f'Use format `YYYY-MM-DDM`\\.',
                parse_mode=ParseModes.MARKDOWN_V2,
                reply_markup=reply_markup_for_waiting_of_answer,
            )
            return

        today_in_user_tz = self.message.from_user.get_today_in_user_tz()

        if new_work_date > today_in_user_tz + datetime.timedelta(days=31):
            await self.message.reply(
                'You cannot edit data for more than a month in advance.',
                reply_markup=reply_markup_for_waiting_of_answer,
            )
            return

        if new_work_date < today_in_user_tz - datetime.timedelta(days=365 * 3):
            await self.message.reply(
                'You cannot edit data created more than 3 years ago.',
                reply_markup=reply_markup_for_waiting_of_answer,
            )
            return

        await user_manager.set_work_date(new_work_date)
        await user_manager.clear_waiting_of_answer()
        await self.message.reply(
            (
                'The work date successfully updated\\.\n'
                f'Your current work date: `{self.message.from_user.get_selected_work_date()}`'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
        )


class ResetWorkDate(BaseHandler):
    name = CallbackCommands.RESET_WORK_DATE
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, *args) -> None:
        user_manager = UserManager(user=self.message.from_user)
        await user_manager.set_work_date(None)

        await self.message.answer(
            f'Successfully reset {emojize(":thumbs_up:")}',
        )
