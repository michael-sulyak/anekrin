import datetime
import typing

from aiogram.utils.markdown import escape_md

from .. import constants
from ..exceptions import ValidationError
from ... import models


async def recalculate_day_bonus(date: datetime.date, *, user: models.User, _max_next_days_to_check: int = 29) -> int:
    # Note: Need to run with lock by a user

    from .work_log_stats import WorkLogsStats

    next_date = date + datetime.timedelta(days=1)

    work_logs_stats = WorkLogsStats()
    await work_logs_stats.set_data_from_db_for_period(
        date_range=(date, next_date,),
        for_user=user,
    )

    day_score = work_logs_stats.get_day_score(date)
    bonus = (day_score - constants.TARGET_NUMBER) // 2

    work_log = await models.WorkLog.filter(
        type=constants.WorkLogTypes.BONUS,
        date=next_date,
        owner=user,
    ).first()

    if not work_log:
        work_log = models.WorkLog(
            name='',
            type=constants.WorkLogTypes.BONUS,
            date=next_date,
            owner=user,
            reward=0,
        )

    saved_bonus = work_log.reward

    if bonus == saved_bonus:
        return 0

    work_log.reward = bonus

    if work_log.reward <= 0:
        if work_log.id is None:
            result = 0
        else:
            # Don't save negative bonus.
            await work_log.delete()
            result = -saved_bonus
    else:
        if work_log.id is None:
            await work_log.save()
            result = bonus
        else:
            await work_log.save(update_fields=('reward',))
            result = bonus - saved_bonus

    if result != 0 and _max_next_days_to_check > 0:
        old_day_score_for_tomorrow = work_logs_stats.get_day_score(next_date)
        work_logs_stats.add_day_score(score=bonus - saved_bonus, date=next_date)
        new_day_score_for_tomorrow = work_logs_stats.get_day_score(next_date)

        if max(old_day_score_for_tomorrow, new_day_score_for_tomorrow) > constants.TARGET_NUMBER:
            await recalculate_day_bonus(
                next_date,
                user=user,
                _max_next_days_to_check=_max_next_days_to_check - 1,
            )

    return result


async def rewrite_current_user_tasks(tasks_info: typing.List[dict], *, for_user: models.User) -> None:
    # Note: Need to run with lock by a user

    current_categories = tuple(await models.Category.filter(
        owner=for_user,
    ))

    map_of_current_categories = {
        current_category.name: current_category
        for current_category in current_categories
    }

    current_tasks = tuple(await models.Task.filter(
        owner=for_user,
    ))

    map_of_current_tasks = {
        current_task.name: current_task
        for current_task in current_tasks
    }

    tasks_to_update = []
    tasks_to_create = []

    proceed_task_names = set()

    for position, task_info in enumerate(tasks_info, 1):
        task_name = task_info['name']
        task_reward = task_info['reward']
        task_category_name = task_info['category']

        if task_name in proceed_task_names:
            raise ValidationError(f'`{escape_md(task_name)}` is duplicated\\.', is_markdown=True)

        proceed_task_names.add(task_name)

        if task_name in map_of_current_tasks:
            task = map_of_current_tasks[task_name]
            task.position = position
            task.reward = task_reward
            task.category = map_of_current_categories.get(task_category_name)
            tasks_to_update.append(task)
        else:
            tasks_to_create.append(models.Task(
                name=task_name,
                owner=for_user,
                position=position,
                reward=task_reward,
                category=map_of_current_categories.get(task_category_name),
            ))

    task_ids_to_delete = set(task.id for task in current_tasks) - set(task.id for task in tasks_to_update)

    if task_ids_to_delete:
        await models.Task.filter(
            id__in=task_ids_to_delete,
        ).delete()

    if tasks_to_update:
        await models.Task.bulk_update(
            tasks_to_update,
            fields=('position', 'reward', 'category_id',),
        )

    if tasks_to_create:
        await models.Task.bulk_create(
            tasks_to_create,
        )


async def rewrite_current_user_categories(tasks_info: typing.List[dict], *, for_user: models.User) -> None:
    # Note: Need to run with lock by a user

    current_categories = tuple(await models.Category.filter(
        owner=for_user,
    ))

    current_category_names = set(
        current_category.name
        for current_category in current_categories
    )

    new_category_names = set(
        task_info['category']
        for task_info in tasks_info
    )

    categories_to_create = tuple(
        models.Category(name=new_category_name, owner=for_user)
        for new_category_name in new_category_names
        if new_category_name is not None and new_category_name not in current_category_names
    )

    category_ids_to_delete = tuple(
        current_category.id
        for current_category in current_categories
        if current_category.name not in new_category_names
    )

    if category_ids_to_delete:
        await models.Category.filter(
            id__in=category_ids_to_delete,
        ).delete()

    if categories_to_create:
        await models.Category.bulk_create(
            categories_to_create,
        )
