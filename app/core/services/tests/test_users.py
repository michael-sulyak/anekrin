import datetime

import pytest

from ..users import UserManager
from .... import models
from ....common.tests.utils import generate_random_telegram_user


@pytest.mark.asyncio
async def test_user_manager__get_user_by_telegram_user() -> None:
    telegram_user = generate_random_telegram_user()
    user, created = await UserManager.get_user_by_telegram_user(telegram_user)

    assert created
    assert user.telegram_user_id == telegram_user.id
    assert await models.User.all().count() == 1
    assert await models.User.filter(telegram_user_id=telegram_user.id).exists()


@pytest.mark.asyncio
async def test_user_manager__get_user_by_telegram_user_with_user() -> None:
    telegram_user = generate_random_telegram_user()

    created_user = await models.User.create(telegram_user_id=telegram_user.id)
    user, created = await UserManager.get_user_by_telegram_user(telegram_user)

    assert not created
    assert user.id == created_user.id
    assert user.telegram_user_id == telegram_user.id
    assert await models.User.all().count() == 1
    assert await models.User.filter(id=created_user.id).exists()


@pytest.mark.asyncio
async def test_user_manager__set_work_date() -> None:
    telegram_user = generate_random_telegram_user()
    user = await models.User.create(telegram_user_id=telegram_user.id)
    user_manager = UserManager(user=user)

    assert user.selected_work_date is None

    date = datetime.date(2010, 1, 1)
    await user_manager.set_work_date(date)

    assert user.selected_work_date == date
    assert await models.User.filter(id=user.id, selected_work_date=date).exists()


@pytest.mark.asyncio
async def test_user_manager__reset_work_date() -> None:
    telegram_user = generate_random_telegram_user()
    date = datetime.date(2010, 1, 1)
    user = await models.User.create(
        telegram_user_id=telegram_user.id,
        selected_work_date=date,
    )
    user_manager = UserManager(user=user)

    assert user.selected_work_date == date

    await user_manager.set_work_date(None)

    assert user.selected_work_date is None
    assert await models.User.filter(id=user.id, selected_work_date__isnull=True).exists()
