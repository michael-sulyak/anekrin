import datetime
import random
import string
import typing

from aiogram.types import Update as TelegramUpdate, User as TelegramUser, CallbackQuery as TelegramCallbackQuery


DEFAULT_TEST_SENDER = {
    'id': random.randint(1, 1_000_000),
    'is_bot': False,
    'first_name': 'Mike',
    'last_name': 'Freeman',
    'username': 'mike',
    'language_code': 'en',
}

DEFAULT_TEST_CHAT = {
    'id': random.randint(1, 1_000_000),
    'first_name': 'Mike',
    'last_name': 'Freeman',
    'username': 'mike',
    'type': 'private',
}


def generate_telegram_update_for_text(text: str, *, sender: dict) -> TelegramUpdate:
    return TelegramUpdate(
        update_id=random.randint(1, 1_000_000),
        message={
            'message_id': random.randint(1, 1_000_000),
            'from': sender,
            'chat': DEFAULT_TEST_CHAT,
            'date': int(datetime.datetime.now().timestamp()),
            'text': text,
        },
    )


class CustomTelegramCallbackQuery(TelegramCallbackQuery):
    async def answer(self, *args, **kwargs) -> typing.Any:
        pass


def generate_telegram_update_for_callback(callback_query: str, *, sender: dict) -> TelegramUpdate:
    return TelegramUpdate(
        update_id=random.randint(1, 1_000_000),
        callback_query=CustomTelegramCallbackQuery(**{
            'data': callback_query,
            'chat': DEFAULT_TEST_CHAT,
            'from': sender,
        }),
    )


def generate_random_string(n: int) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=n))


def generate_random_raw_user() -> dict:
    return {
        'id': random.randint(1, 1_000_000),
        'is_bot': False,
        'first_name': generate_random_string(10).title(),
        'last_name': generate_random_string(10).title(),
        'username': generate_random_string(10),
        'language_code': 'en',
    }


def generate_random_telegram_user() -> TelegramUser:
    return TelegramUser(**generate_random_raw_user())
