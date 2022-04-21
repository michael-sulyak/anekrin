import datetime
import json
import logging
import typing
from collections import defaultdict
from json import JSONDecodeError

from emoji.core import emojize
from tortoise.functions import Max

from .work_log_stats import WorkLogsStats
from .. import constants
from ..exceptions import ValidationError
from ... import models
from ...models.utils import create_task, create_work_log, lock_by_user


class TaskManager:
    user: models.User

    def __init__(self, *, user: models.User) -> None:
        self.user = user

    async def create_samples(self) -> None:
        await create_task(
            name=f'{emojize(":person_lifting_weights:")} Do exercises',
            reward=20,
            owner=self.user,
        )

        await create_task(
            name=f'{emojize(":person_walking:")} Take a walk',
            reward=15,
            owner=self.user,
        )

        task = await create_task(
            name=f'{emojize(":mobile_phone:")} Open the bot',
            reward=15,
            owner=self.user,
        )

        await self.mark_task_as_completed(task_id=task.id)

    async def get_task(self, task_id: int) -> models.Task:
        task = await models.Task.get(
            id=task_id,
            owner=self.user,
        )
        task.owner = self.user  # To prevent the query
        return task

    async def get_template_for_bulk_task_editing(self) -> str:
        tasks = await self.get_tasks()

        if tasks:
            data = tuple(
                {
                    'name': task.name,
                    'reward': task.reward,
                }
                for task in tasks
            )
        else:
            data = (
                {
                    'name': 'Do exercises',
                    'reward': 20,
                },
                {
                    'name': 'Take a walk',
                    'reward': 30,
                },
            )

        return json.dumps(data, ensure_ascii=False, indent=2)

    def get_template_for_import_task_logs(self) -> str:
        data = {
            self.user.get_selected_work_date().isoformat(): [
                {
                    'name': 'Do exercises',
                    'reward': 20,
                },
                {
                    'name': 'Take a walk',
                    'reward': 30,
                },
            ],
        }

        return json.dumps(data, ensure_ascii=False, indent=2)

    async def export_data(self) -> dict[str, str]:
        tasks_info = tuple(await models.Task.filter(
            owner=self.user,
        ).order_by(
            'position',
        ).values(
            'name',
            'reward',
        ))

        work_logs_info = defaultdict(list)

        work_logs = tuple(await models.WorkLog.filter(
            owner=self.user,
        ).order_by(
            'id',
        ).only(
            'date',
            'type',
            'reward',
            'name',
        ))

        for work_log in work_logs:
            work_logs_info[work_log.date.isoformat()].append({
                'name': work_log.showed_name,
                'reward': work_log.reward,
            })

        return {
            'tasks.json': json.dumps(tasks_info, ensure_ascii=False, indent=2),
            'work_logs.json': json.dumps(work_logs_info, ensure_ascii=False, indent=2),
        }

    async def import_work_logs(self, data: dict[list[dict[str, typing.Any]]]) -> None:
        try:
            work_logs = tuple(
                models.WorkLog(
                    type=constants.WorkLogTypes.USER_WORK,
                    name=work_log_info['name'],
                    owner=self.user,
                    date=datetime.date.fromisoformat(date),
                    reward=work_log_info['reward'],
                )
                for date, work_logs_info in data.items()
                for work_log_info in work_logs_info
            )
        except Exception as e:
            logging.error(e)
            raise ValidationError('Wrong data.')

        async with lock_by_user(self.user.id):
            await models.WorkLog.filter(
                owner=self.user,
                date__in=data.keys(),
            ).delete()
            await models.WorkLog.bulk_create(work_logs)

    async def save_tasks_info(self, tasks_info: str) -> None:
        try:
            tasks_info = json.loads(tasks_info)
        except JSONDecodeError:
            raise ValidationError('JSON is invalid.')

        async with lock_by_user(self.user.id):
            current_tasks = tuple(await models.Task.filter(
                owner=self.user,
            ))

            current_tasks_map = {
                current_task.name: current_task
                for current_task in current_tasks
            }

            tasks_to_update = []
            tasks_to_create = []

            proceed_task_names = set()

            for position, task_info in enumerate(tasks_info, 1):
                task_name = task_info['name']
                task_reward = task_info['reward']

                if task_name in proceed_task_names:
                    continue

                proceed_task_names.add(task_name)

                if task_name in current_tasks_map:
                    task = current_tasks_map[task_name]
                    task.position = position
                    task.reward = task_reward
                    tasks_to_update.append(task)
                else:
                    tasks_to_create.append(models.Task(
                        name=task_name,
                        owner=self.user,
                        position=position,
                        reward=task_reward,
                    ))

            task_ids_to_delete = (
                    set(task.id for task in current_tasks)
                    - set(task.id for task in tasks_to_update)
            )

            if task_ids_to_delete:
                await models.Task.filter(
                    id__in=task_ids_to_delete,
                ).delete()

            if tasks_to_update:
                await models.Task.bulk_update(
                    tasks_to_update,
                    fields=('position', 'reward',),
                )

            if tasks_to_create:
                await models.Task.bulk_create(
                    tasks_to_create,
                )

    @staticmethod
    async def update_task_name(*, task: models.Task, new_name: str) -> None:
        task.name = new_name
        await task.save(update_fields=('name',))

    @staticmethod
    async def update_task_reward(*, task: models.Task, new_reward: int) -> None:
        task.reward = new_reward
        await task.save(update_fields=('reward',))

    async def update_task_position(self, *, task: models.Task, new_task_position: int) -> None:
        async with lock_by_user(task.owner.id):
            tasks = list(await self.get_tasks())

            for i, task_ in enumerate(tasks):
                if task_.id == task.id:
                    task = tasks[i]
                    break

            if not (1 <= new_task_position <= len(tasks) + 1):
                raise ValidationError(
                    'Invalid position.'
                    f'Available choices: 1-{len(tasks) + 1}'
                )

            if new_task_position == len(tasks) + 1:
                position = 1

                for task_ in tasks:
                    if task_.id == task.id:
                        continue

                    task_.position = position
                    position += 1

                task.position = position
            elif task.position < new_task_position:
                position = task.position

                for task_ in tasks[task.position:]:
                    if position == new_task_position:
                        position += 1

                    task_.position = position
                    position += 1

                task.position = new_task_position
            elif task.position > new_task_position:
                position = new_task_position + 1

                for task_ in tasks[new_task_position - 1:]:
                    if task_.id == task.id:
                        continue

                    task_.position = position
                    position += 1

                task.position = new_task_position
            else:
                return

            await models.Task.bulk_update(tasks, fields=('position',))

    async def get_tasks(self) -> typing.Tuple[models.Task, ...]:
        return tuple(await models.Task.filter(
            owner=self.user,
        ).order_by(
            'position',
        ))

    async def get_tasks_with_last_work_log_date(self) -> typing.Tuple[models.Task, ...]:
        return tuple(await models.Task.filter(
            owner=self.user,
        ).annotate(
            last_work_log_date=Max('work_logs__date'),
        ).order_by(
            'position',
        ))

    async def mark_task_as_completed(self, *, task_id: int) -> typing.Dict[str, typing.Any]:
        async with lock_by_user(self.user.id):
            task = await models.Task.filter(
                id=task_id,
                owner=self.user,
            ).first()

            if not task:
                raise ValidationError('The task does\'s exist.')

            task.owner = self.user  # To prevent a query

            work_log = await create_work_log(task=task)

            day_bonus = await self._recalculate_day_bonus(date=work_log.date)

        return {
            'day_bonus': day_bonus,
        }

    async def get_work_logs(self, *, type_: typing.Optional[str] = None) -> typing.Tuple[models.WorkLog, ...]:
        additional_filter = {}

        if type_ is not None:
            additional_filter['type'] = type_

        return tuple(await models.WorkLog.filter(
            owner=self.user,
            date=self.user.get_selected_work_date(),
        ).filter(
            **additional_filter,
        ).order_by(
            'id',
        ))

    async def delete_task(self, *, task_id: int) -> None:
        async with lock_by_user(self.user.id):
            task = await models.Task.filter(
                id=task_id,
                owner=self.user,
            ).first()

            if not task:
                return

            other_tasks = tuple(await models.Task.filter(
                owner=self.user,
                position__gt=task.position,
            ).order_by(
                'position',
            ))

            await task.delete()

            if not other_tasks:
                return

            for new_order, task in enumerate(other_tasks, task.position):
                task.position = new_order

            await models.Task.bulk_update(other_tasks, fields=('position',))

    async def get_work_log(self, work_log_id: int) -> typing.Optional[models.WorkLog]:
        return await models.WorkLog.filter(
            id=work_log_id,
            owner=self.user,
        ).first()

    async def delete_work_log(self, work_log_id: int) -> dict[str, typing.Any]:
        async with lock_by_user(self.user.id):
            work_log = await self.get_work_log(work_log_id)

            if not work_log:
                raise ValidationError('This post has already been deleted.')

            date = work_log.date
            await work_log.delete()

            day_bonus = await self._recalculate_day_bonus(date)

        return {
            'day_bonus': day_bonus,
        }

    async def _recalculate_day_bonus(self, date: datetime.date, *, _max_next_days_to_check: int = 6) -> int:
        # Note: Need to run with lock by a user

        next_date = date + datetime.timedelta(days=1)

        work_logs_stats = WorkLogsStats()
        await work_logs_stats.set_data_from_db_for_period(
            date_range=(date, next_date,),
            for_user=self.user,
        )

        day_score = work_logs_stats.get_day_score(date)
        bonus = (day_score - constants.TARGET_NUMBER) // 2

        work_log = await models.WorkLog.filter(
            type=constants.WorkLogTypes.BONUS,
            date=next_date,
            owner=self.user,
        ).first()

        if not work_log:
            work_log = models.WorkLog(
                name='',
                type=constants.WorkLogTypes.BONUS,
                date=next_date,
                owner=self.user,
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
                await self._recalculate_day_bonus(
                    next_date,
                    _max_next_days_to_check=_max_next_days_to_check - 1,
                )

        return result
