from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from emoji.core import emojize

from ..base import BaseHandler
from ..constants import HandlerTypes
from ...constants import BotCommand, CallbackCommands, TARGET_NUMBER
from ...services.users import UserManager


__all__ = (
    'Start',
    'Help',
    'CancelQuestion',
)


class Start(BaseHandler):
    name = BotCommand.START
    type = HandlerTypes.MESSAGE

    async def handle(self) -> None:
        await self.message.answer('Hello! What have you done usefully today?')
        await Help(message=self.message).handle()
        await self.message.answer(
            f'{emojize(":information:")} Don\'t forget to update your time zone in the settings.',
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        f'{emojize(":two-thirty:")} Change time zone',
                        callback_data=CallbackCommands.UPDATE_TIMEZONE,
                    ),
                ]],
            )
        )


class Help(BaseHandler):
    name = CallbackCommands.HELP
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        await self.message.answer(
            (
                '*Anekrin* is a simple task manager for evaluating daily personal performance in routine tasks\\.\n\n'
                f'*{emojize(":chequered_flag:")} How to start?*\n\n'
                f'*{emojize(":keycap_1:")} Create a list of tasks on which you evaluate your performance\\.*\n'
                'For example: `Watch one video lesson`, `Go to the gym`, etc\\.\n\n'
                f'*{emojize(":keycap_2:")} Set a reward for each task\\.*\n'
                f'Every day you must strive to score {TARGET_NUMBER} points\\.\n'
                'For example: I worked in the office yesterday \\(\\+50\\), '
                'read a book a little \\(\\+20\\), went for a walk \\(\\+30\\)\\.\n'
                'And tomorrow, instead of a walk, I watched a video lesson \\(\\+30\\) and as a result, '
                'it also turned out to be a productive day\\.\n\n'
                f'*{emojize(":keycap_3:")} Strive to have *"average"* equal to 100\\.*\n'
                'This is the sum of accumulated points for 7 days divided by 7\\.\n'
                'Why? Because one day your productivity can be low, and the next day it can be high\\. '
                'As a result, it is more useful to know the *"average"* for the last seven days\\.\n\n'
                f'*Now just try it* {emojize(":winking_face:")}'
            ),
            parse_mode=ParseMode.MARKDOWN_V2,
        )


class CancelQuestion(BaseHandler):
    name = CallbackCommands.CANCEL_QUESTION
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        user_manager = UserManager(user=self.message.from_user)

        await user_manager.clear_waiting_of_answer()
        await self.message.answer(
            f'Canceled {emojize(":thumbs_up:")}\n'
            f'You can select another action.'
        )
