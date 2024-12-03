from aiogram import Bot as TelegramBot
from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton,
    ReplyKeyboardMarkup,
)
from emoji.core import emojize

from . import constants
from .base import BaseMessage
from .. import config


def get_main_reply_keyboard_markup() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[
            KeyboardButton(text=constants.BotCommand.SHOW_TASKS),
            KeyboardButton(text=constants.BotCommand.SHOW_STATS),
            KeyboardButton(text=constants.BotCommand.SHOW_SETTING),
        ]],
        resize_keyboard=True,
    )


def get_reply_for_cancel_question(name: str = 'Cancel') -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[get_btn_for_cancel_question(name)]],
    )


def get_btn_for_cancel_question(name: str = 'Cancel') -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=f'{emojize(":multiply:")} {name}',
        callback_data=constants.CallbackCommands.CANCEL_QUESTION,
    )


def get_btn_for_reset_work_date(name: str = 'Reset & Use the current day') -> InlineKeyboardButton:
    return InlineKeyboardButton(
        text=f'{emojize(":spiral_calendar:")} {name}',
        callback_data=constants.CallbackCommands.RESET_WORK_DATE,
    )


async def send_not_found(message: BaseMessage) -> None:
    await message.reply(
        f'The command is not found {emojize(":sad_but_relieved_face:")}',
        reply_markup=get_main_reply_keyboard_markup(),
    )


async def send_not_found_for_question(message: BaseMessage) -> None:
    await message.reply(
        'The answer is invalid. Try to repeat.',
        reply_markup=get_main_reply_keyboard_markup(),
    )


def get_emojize_for_score(score: int) -> str:
    if score >= constants.TARGET_NUMBER * 1.5:
        return emojize(':fire:')
    elif score >= constants.TARGET_NUMBER * 1.2:
        return emojize(':smiling_face_with_heart-eyes:')
    elif score > constants.TARGET_NUMBER:
        return emojize(':smiling_face_with_sunglasses:')
    elif score == constants.TARGET_NUMBER:
        return emojize(':OK_hand:')
    elif score >= constants.TARGET_NUMBER * 0.8:
        return emojize(':thumbs_up:')
    elif score >= constants.TARGET_NUMBER * 0.6:
        return emojize(':slightly_smiling_face:')
    elif score >= constants.TARGET_NUMBER * 0.2:
        return emojize(':face_with_rolling_eyes:')
    else:
        return emojize(':neutral_face:')


def get_day_performance_info(*, day_score: int, week_average: int) -> str:
    return (
        f'*Performance:*\n'
        f'{emojize(":calendar:")} *Today:* `{day_score}` {get_emojize_for_score(day_score)}\n'
        f'{emojize(":spiral_calendar:")} *Average:* `{week_average}` {get_emojize_for_score(week_average)}'
    )


def init_telegram_bot() -> TelegramBot:
    return TelegramBot(token=config.TELEGRAM_API_TOKEN)
