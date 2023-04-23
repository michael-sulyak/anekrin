import abc
import datetime
import io
import json
import logging

from aiogram.types import (
    Document as TelegramDocument, InlineKeyboardButton, InlineKeyboardMarkup,
    InputFile as TelegramInputFile,
)
from aiogram.utils.markdown import escape_md
from emoji.core import emojize
from tortoise.exceptions import DoesNotExist

from ..base import BaseHandler
from ..constants import HandlerTypes
from ..utils.for_answers import get_text_complete_button, get_text_for_new_day_bonus
from ..utils.throttling import with_throttling
from ... import constants
from ...constants import BotCommand, CallbackCommands, ParseModes, QuestionTypes
from ...exceptions import ValidationError
from ...services.categories import CategoryManager
from ...services.tasks import TaskManager
from ...services.users import UserManager
from ...services.work_log_stats import WorkLogsStats
from ...utils import get_day_performance_info, get_emojize_for_score, get_reply_for_cancel_question
from .... import models


__all__ = (
    'ShowTasks',
    'ShowFinishedTask',
    'ShowStats',
    'DeleteWorkLog',
    'CompleteTask',
    'DeleteTask',
    'EditTask',
    'CreateTask',
    'AnswerWithNameForNewTask',
    'AnswerWithNewTaskReward',
    'AnswerWithNewNameForTask',
    'ChangeTaskReward',
    'ChangeTaskName',
    'ChangeTaskPosition',
    'AnswerWithNewTaskPosition',
    'RewriteAllTasks',
    'AnswerWithTaskInfo',
    'ShowCalendarHeatmap',
    'ImportWorkLogs',
    'AnswerWithWorkLogs',
    'ExportData',
    'ShowDetailedStats',
)


class ShowTasks(BaseHandler):
    name = BotCommand.SHOW_TASKS
    type = HandlerTypes.MESSAGE

    async def handle(self, selected_category_id: str | None = None) -> None:
        task_manager = TaskManager(user=self.message.from_user)
        category_manager = CategoryManager(user=self.message.from_user)

        tasks = await task_manager.get_tasks_with_count_of_work_logs()
        show_tasks = True

        if selected_category_id:
            if selected_category_id == 'other':
                selected_category_name = 'Other tasks'
                tasks = tuple(
                    task
                    for task in tasks
                    if task.category_id is None
                )
            else:
                selected_category_id = int(selected_category_id)
                selected_category = await category_manager.get_category(selected_category_id)
                selected_category_name = selected_category.name
                tasks = tuple(
                    task
                    for task in tasks
                    if task.category_id == selected_category_id
                )
        else:
            selected_category_name = None

        if self.message.from_user.selected_work_date:
            await self.message.answer(
                f'Selected date: `{self.message.from_user.selected_work_date}`',
                parse_mode=ParseModes.MARKDOWN_V2,
            )

        inline_markup_for_creating = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(
                    f'{emojize(":plus:")} Add task',
                    callback_data=CallbackCommands.CREATE_TASK,
                ),
                InlineKeyboardButton(
                    f'{emojize(":plus:")} Add category',
                    callback_data=CallbackCommands.CREATE_CATEGORY,
                ),
            ]],
        )

        if not tasks:
            await self.message.answer(
                f'You don\'t have tasks {emojize(":sad_but_relieved_face:")}',
                reply_markup=inline_markup_for_creating,
            )
            return

        if not selected_category_id:
            categories = await category_manager.get_categories()

            if categories:
                inline_keyboard_with_categories = [
                    [
                        InlineKeyboardButton(
                            category.name,
                            callback_data=f'{CallbackCommands.SHOW_TASKS_IN_CATEGORY} {category.id}',
                        ),
                    ]
                    for category in categories
                ]

                has_tasks_without_category = any(
                    task.category_id is None
                    for task in tasks
                )

                if has_tasks_without_category:
                    inline_keyboard_with_categories.append([
                        InlineKeyboardButton(
                            'Other',
                            callback_data=f'{CallbackCommands.SHOW_TASKS_IN_CATEGORY} other',
                        ),
                    ])

                await self.message.answer(
                    'Choose a category:',
                    reply_markup=InlineKeyboardMarkup(
                        inline_keyboard=inline_keyboard_with_categories,
                    ),
                )

                show_tasks = False

        if show_tasks:
            if selected_category_name is None:
                await self.message.answer('Your current tasks:')
            else:
                await self.message.answer(f'Your current tasks in category "{selected_category_name}":')

            for task in tasks:
                inline_keyboard = [[
                    InlineKeyboardButton(
                        get_text_complete_button(task.count_of_work_logs_for_current_date),
                        callback_data=f'{CallbackCommands.COMPLETE_TASK} {task.id}',
                    ),
                    InlineKeyboardButton(
                        f'{emojize(":pencil:")} Edit',
                        callback_data=f'{CallbackCommands.EDIT_TASK} {task.id}',
                    ),
                ]]

                await self.message.answer(
                    f'{task.position}\\. {escape_md(task.name)} `({task.str_reward})`',
                    parse_mode=ParseModes.MARKDOWN_V2,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=inline_keyboard),
                )

        await self.message.answer(
            'Or do you want to do something else?',
            reply_markup=inline_markup_for_creating,
        )


class ShowTasksInCategory(BaseHandler):
    name = CallbackCommands.SHOW_TASKS_IN_CATEGORY
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, selected_category_id: str) -> None:
        await ShowTasks(message=self.message).handle(selected_category_id=selected_category_id)


class ShowFinishedTask(BaseHandler):
    name = CallbackCommands.SHOW_FINISHED_TASKS
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        task_manager = TaskManager(user=self.message.from_user)
        work_logs = await task_manager.get_work_logs(type_=constants.WorkLogTypes.USER_WORK)
        date = self.message.from_user.get_selected_work_date().isoformat()

        if not work_logs:
            await self.message.answer(
                f'You don\'t have finished tasks for `{date}`\\.',
                parse_mode=ParseModes.MARKDOWN_V2,
            )
            return

        await self.message.answer(
            f'Your finished tasks for `{date}`:',
            parse_mode=ParseModes.MARKDOWN_V2,
        )

        for work_log in work_logs:
            if work_log.reward > 0:
                reward = f'+{work_log.reward}'
            else:
                reward = str(work_log.reward)

            await self.message.answer(
                f'{escape_md(work_log.name)} `({reward})`',
                parse_mode=ParseModes.MARKDOWN_V2,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(
                        f'{emojize(":wastebasket:")} Delete',
                        callback_data=f'{CallbackCommands.DELETE_WORK_LOG} {work_log.id}',
                    ),
                ]]),
            )


class CompleteTask(BaseHandler):
    name = CallbackCommands.COMPLETE_TASK
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, task_id: str) -> None:
        task_manager = TaskManager(user=self.message.from_user)

        task_id = int(task_id)
        task = await task_manager.get_task(task_id)

        result = await task_manager.mark_task_as_completed(task_id=task_id)
        count_of_work_logs = await task_manager.get_count_of_work_logs_for_current_date(task_id=task_id)

        await self.message.edit_reply_markup(
            InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    get_text_complete_button(count_of_work_logs),
                    callback_data=f'{CallbackCommands.COMPLETE_TASK} {task.id}',
                ),
                InlineKeyboardButton(
                    f'{emojize(":pencil:")} Edit',
                    callback_data=f'{CallbackCommands.EDIT_TASK} {task.id}',
                ),
            ]]),
        )

        work_date = self.message.from_user.get_selected_work_date()

        work_logs_stats = WorkLogsStats()
        await work_logs_stats.set_data_from_db_for_date(
            date=work_date,
            for_user=self.message.from_user,
        )

        day_score = work_logs_stats.get_day_score(work_date)
        week_average = work_logs_stats.get_week_average(work_date)

        await self.message.answer(
            (
                f'Marked as completed \\(`{task.str_reward}`\\) {emojize(":thumbs_up:")}\n\n'
                f'{get_day_performance_info(day_score=day_score, week_average=week_average)}'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
        )

        day_bonus = result['day_bonus']

        if day_bonus != 0:
            await self.message.answer(
                get_text_for_new_day_bonus(day_bonus),
                parse_mode=ParseModes.MARKDOWN_V2,
            )

        if day_score >= constants.TARGET_NUMBER:
            # Check previous value
            work_logs_stats.add_day_score(score=-task.reward, date=work_date)
            old_day_score = work_logs_stats.get_day_score(work_date)
            work_logs_stats.add_day_score(score=task.reward, date=work_date)

            if old_day_score < constants.TARGET_NUMBER:
                await self.message.answer(
                    f'Good job! Now you can rest easy {emojize(":relieved_face:")}',
                )


class ShowOldTasks(BaseHandler):
    name = CallbackCommands.SHOW_OLD_TASKS
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        old_tasks, remark = await self._get_old_tasks()

        if not old_tasks:
            await self.message.answer(f'I didn\'t find old tasks. You are awesome {emojize(":relieved_face:")}')
            return

        old_tasks_info = '\n'.join(
            f'{emojize(":black_small_square:")} {escape_md(task.name)}'
            for task in old_tasks[:5]
        )

        await self.message.answer(
            f'{old_tasks_info}\n\n{remark}',
            parse_mode=ParseModes.MARKDOWN_V2,
        )

    async def _get_old_tasks(self) -> tuple[tuple[models.Task, ...], str]:
        task_manager = TaskManager(user=self.message.from_user)

        tasks = await task_manager.get_tasks_with_last_work_log_date()

        sorted_tasks = sorted(
            tasks,
            key=lambda x: (
                datetime.date.min if x.last_work_log_date is None else x.last_work_log_date,
                x.position,
            ),
        )

        selected_work_date = self.message.from_user.get_selected_work_date()
        check_before = self.message.from_user.get_selected_work_date() - datetime.timedelta(days=6)
        day_ago = datetime.datetime.now().astimezone() - datetime.timedelta(days=1)

        old_tasks = tuple(
            task
            for task in sorted_tasks
            if (
                    (task.last_work_log_date is not None and task.last_work_log_date <= check_before)
                    or (task.last_work_log_date is None and task.created_at <= day_ago)
            )
        )

        if old_tasks:
            remark = (
                f'You didn\'t forget about {"this task" if len(old_tasks) == 1 else "these tasks"}? '
                f'{emojize(":face_with_monocle:")}'
            )
        else:
            old_tasks = tuple(
                task
                for task in sorted_tasks
                if task.last_work_log_date != selected_work_date
            )
            remark = f'If you are in the mood, you can take on these tasks {emojize(":winking_face:")}'

        return old_tasks, remark


class CreateTask(BaseHandler):
    name = CallbackCommands.CREATE_TASK
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        user_manager = UserManager(user=self.message.from_user)

        await user_manager.wait_answer_for(QuestionTypes.NAME_FOR_NEW_TASK)
        await self.message.answer(
            'Enter task name:',
            reply_markup=get_reply_for_cancel_question(),
        )


class CreateCategory(BaseHandler):
    name = CallbackCommands.CREATE_CATEGORY
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        user_manager = UserManager(user=self.message.from_user)

        await user_manager.wait_answer_for(QuestionTypes.NAME_FOR_NEW_CATEGORY)
        await self.message.answer(
            'Enter category name:',
            reply_markup=get_reply_for_cancel_question(),
        )


class BaseHandlerForTaskFieldUpdating(BaseHandler, abc.ABC):
    type = HandlerTypes.CALLBACK_QUERY
    question_type: str

    async def handle(self, task_id: str) -> None:
        user_manager = UserManager(user=self.message.from_user)
        task_manager = TaskManager(user=self.message.from_user)

        task_id = int(task_id)
        task = await task_manager.get_task(task_id)

        await user_manager.wait_answer_for(f'{self.question_type} {task.id}')
        await self._send_prompt(task)

    @abc.abstractmethod
    async def _send_prompt(self, task: models.Task) -> None:
        pass


class BaseHandlerForCategoryFieldUpdating(BaseHandler, abc.ABC):
    type = HandlerTypes.CALLBACK_QUERY
    question_type: str

    async def handle(self, category_id: str) -> None:
        user_manager = UserManager(user=self.message.from_user)
        category_manager = CategoryManager(user=self.message.from_user)

        category_id = int(category_id)
        category = await category_manager.get_category(category_id)

        await user_manager.wait_answer_for(f'{self.question_type} {category.id}')
        await self._send_prompt(category)

    @abc.abstractmethod
    async def _send_prompt(self, category: models.Category) -> None:
        pass


class ChangeTaskName(BaseHandlerForTaskFieldUpdating):
    name = CallbackCommands.CHANGE_TASK_NAME
    question_type = QuestionTypes.CHANGE_TASK_NAME

    async def _send_prompt(self, task: models.Task) -> None:
        await self.message.answer('You want to update the name for task:')
        await self.message.answer(
            f'`{escape_md(task.name)}`',
            parse_mode=ParseModes.MARKDOWN_V2,
        )
        await self.message.answer(
            'Enter the new task name:',
            reply_markup=get_reply_for_cancel_question(),
        )


class ChangeCategoryName(BaseHandlerForCategoryFieldUpdating):
    name = CallbackCommands.CHANGE_CATEGORY_NAME
    question_type = QuestionTypes.CHANGE_CATEGORY_NAME

    async def _send_prompt(self, category: models.Task) -> None:
        await self.message.answer('You want to update the name for category:')
        await self.message.answer(
            f'`{escape_md(category.name)}`',
            parse_mode=ParseModes.MARKDOWN_V2,
        )
        await self.message.answer(
            'Enter the new category name:',
            reply_markup=get_reply_for_cancel_question(),
        )


class ChangeTaskReward(BaseHandlerForTaskFieldUpdating):
    name = CallbackCommands.CHANGE_TASK_REWARD
    question_type = QuestionTypes.CHANCE_TASK_REWARD

    async def _send_prompt(self, task: models.Task) -> None:
        await self.message.answer(
            (
                f'You want to update the task reward:\n'
                f'`{escape_md(task.name)}`\n\n'
                f'Enter the new task reward:'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
            reply_markup=get_reply_for_cancel_question(),
        )


class RewriteAllTasks(BaseHandler):
    name = CallbackCommands.REWRITE_ALL_TASKS
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        task_manager = TaskManager(user=self.message.from_user)
        user_manager = UserManager(user=self.message.from_user)

        await user_manager.wait_answer_for(QuestionTypes.INFO_ABOUT_TASKS)
        await self.message.answer('Example:')
        await self.message.answer(await task_manager.get_template_for_bulk_task_editing())
        await self.message.answer(
            (
                f'{emojize(":warning:")} It will replace all your tasks.\n\n'
                f'Enter data:'
            ),
            reply_markup=get_reply_for_cancel_question(),
        )


class AnswerWithTaskInfo(BaseHandler):
    name = QuestionTypes.INFO_ABOUT_TASKS
    type = HandlerTypes.ANSWER

    @with_throttling(datetime.timedelta(hours=3), count=3)
    async def handle(self, tasks_info: str) -> None:
        task_manager = TaskManager(user=self.message.from_user)
        user_manager = UserManager(user=self.message.from_user)

        try:
            await task_manager.save_tasks_info(tasks_info)
        except ValidationError as e:
            await self.message.answer_error(
                e,
                reply_markup=get_reply_for_cancel_question('Cancel editing'),
            )
            return
        except Exception as e:
            logging.exception(e)
            await self.message.answer(
                'Error. Check your data.',
                reply_markup=get_reply_for_cancel_question('Cancel editing'),
            )
            return

        await user_manager.clear_waiting_of_answer()

        await self.message.answer(f'Saved {emojize(":thumbs_up:")}')


class ChangeTaskPosition(BaseHandler):
    name = CallbackCommands.CHANGE_TASK_POSITION
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, task_id: str) -> None:
        user_manager = UserManager(user=self.message.from_user)
        task_manager = TaskManager(user=self.message.from_user)

        task_id = int(task_id)
        tasks = await task_manager.get_tasks()

        answer = 'All tasks:\n'
        for task in tasks:
            task_info = f'{task.position}\\. `{escape_md(task.name)}`'

            if task.id == task_id:
                task_info = f'{emojize(":round_pushpin:")} *{task_info}*'

            answer += task_info + '\n'

        answer += '\nEnter the new task position:'

        await user_manager.wait_answer_for(f'{QuestionTypes.NEW_TASK_POSITION} {task_id}')
        await self.message.answer(
            answer,
            parse_mode=ParseModes.MARKDOWN_V2,
            reply_markup=get_reply_for_cancel_question('Cancel position updating'),
        )


class ChangeTaskCategory(BaseHandler):
    name = CallbackCommands.CHANGE_TASK_CATEGORY
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, task_id: str) -> None:
        category_manager = CategoryManager(user=self.message.from_user)

        categories = await category_manager.get_categories()

        inline_keyboard_with_categories = [
            [
                InlineKeyboardButton(
                    category.name,
                    callback_data=f'{CallbackCommands.SET_TASK_CATEGORY} {task_id} {category.id}',
                ),
            ]
            for category in categories
        ]

        inline_keyboard_with_categories.append([
            InlineKeyboardButton(
                f'{emojize(":wastebasket:")} Reset category',
                callback_data=f'{CallbackCommands.SET_TASK_CATEGORY} {task_id} null',
            ),
        ])

        await self.message.answer(
            'Choose the new category:',
            parse_mode=ParseModes.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=inline_keyboard_with_categories,
            ),
        )


class SetTaskCategory(BaseHandler):
    name = CallbackCommands.SET_TASK_CATEGORY
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, task_id: str, category_id: str) -> None:
        user_manager = UserManager(user=self.message.from_user)
        task_manager = TaskManager(user=self.message.from_user)
        category_manager = CategoryManager(user=self.message.from_user)

        task_id = int(task_id)
        task = await task_manager.get_task(task_id)

        if category_id == 'null':
            new_category = None
        else:
            category_id = int(category_id)
            new_category = await category_manager.get_category(category_id)

        old_category = task.category
        await task_manager.update_task_category(task=task, new_category=new_category)
        await user_manager.clear_waiting_of_answer()

        old_category_name = old_category.name if old_category else ''
        new_category_name = new_category.name if new_category else ''

        await self.message.reply(
            (
                'You successfully changed the task category\\!\n\n'
                f'*The old category*:\n`{escape_md(old_category_name)}`\n\n'
                f'*The new category*:\n`{escape_md(new_category_name)}`\n'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
        )


class AnswerWithNewTaskPosition(BaseHandler):
    name = QuestionTypes.NEW_TASK_POSITION
    type = HandlerTypes.ANSWER

    async def handle(self, new_task_position: str, task_id: str) -> None:
        if new_task_position.isdigit():
            new_task_position = int(new_task_position)
        else:
            await self.message.answer(
                f'`{escape_md(new_task_position)}` is invalid value\\.',
                parse_mode=ParseModes.MARKDOWN_V2,
                reply_markup=get_reply_for_cancel_question('Cancel position updating'),
            )
            return

        user_manager = UserManager(user=self.message.from_user)
        task_manager = TaskManager(user=self.message.from_user)

        task_id = int(task_id)
        task = await task_manager.get_task(task_id)

        try:
            await task_manager.update_task_position(
                task=task,
                new_task_position=new_task_position,
            )
        except ValidationError as e:
            await self.message.answer_error(e)
            return

        await user_manager.clear_waiting_of_answer()

        await self.message.reply(
            f'You successfully updated the task position {emojize(":thumbs_up:")}',
        )


class AnswerWithNameForNewTask(BaseHandler):
    name = QuestionTypes.NAME_FOR_NEW_TASK
    type = HandlerTypes.ANSWER

    async def handle(self, task_name: str) -> None:
        user_manager = UserManager(user=self.message.from_user)
        task_manager = TaskManager(user=self.message.from_user)

        try:
            task = await task_manager.create_task(
                name=task_name,
                reward=0,
            )
        except ValidationError as e:
            await self.message.answer_error(e)
            return
        finally:
            await user_manager.clear_waiting_of_answer()

        await self.message.reply(
            f'You successfully created the new task {emojize(":party_popper:")}',
        )

        await EditTask(message=self.message).handle(str(task.id))


class AnswerWithNameForNewCategory(BaseHandler):
    name = QuestionTypes.NAME_FOR_NEW_CATEGORY
    type = HandlerTypes.ANSWER

    async def handle(self, category_name: str) -> None:
        user_manager = UserManager(user=self.message.from_user)
        category_manager = CategoryManager(user=self.message.from_user)

        try:
            category = await category_manager.create_category(
                name=category_name,
            )
        except ValidationError as e:
            await self.message.answer_error(e)
            return
        finally:
            await user_manager.clear_waiting_of_answer()

        await self.message.reply(
            f'You successfully created the new category {emojize(":party_popper:")}',
        )

        await EditCategory(message=self.message).handle(str(category.id))


class AnswerWithNewNameForTask(BaseHandler):
    name = QuestionTypes.CHANGE_TASK_NAME
    type = HandlerTypes.ANSWER

    async def handle(self, task_name: str, task_id: str) -> None:
        task_id = int(task_id)

        user_manager = UserManager(user=self.message.from_user)
        task_manager = TaskManager(user=self.message.from_user)

        task = await task_manager.get_task(task_id)

        old_name = task.name
        await task_manager.update_task_name(task=task, new_name=task_name)
        await user_manager.clear_waiting_of_answer()
        await self.message.reply(
            (
                'You successfully changed the task name\\!\n\n'
                f'*The old name*:\n`{escape_md(old_name)}`\n\n'
                f'*The new name*:\n`{escape_md(task.name)}`\n'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
        )


class AnswerWithNewNameForCategory(BaseHandler):
    name = QuestionTypes.CHANGE_CATEGORY_NAME
    type = HandlerTypes.ANSWER

    async def handle(self, category_name: str, category_id: str) -> None:
        category_id = int(category_id)

        user_manager = UserManager(user=self.message.from_user)
        category_manager = CategoryManager(user=self.message.from_user)

        try:
            category = await category_manager.get_category(category_id)
        except DoesNotExist:
            await self.message.reply('This category does not exist')
            return

        old_name = category.name
        await category_manager.update_category_name(category=category, new_name=category_name)
        await user_manager.clear_waiting_of_answer()
        await self.message.reply(
            (
                'You successfully changed the category name\\!\n\n'
                f'*The old name*:\n`{escape_md(old_name)}`\n\n'
                f'*The new name*:\n`{escape_md(category.name)}`\n'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
        )


class AnswerWithNewTaskReward(BaseHandler):
    name = QuestionTypes.CHANCE_TASK_REWARD
    type = HandlerTypes.ANSWER

    async def handle(self, task_reward: str, task_id: str) -> None:
        task_id = int(task_id)

        try:
            task_reward = int(task_reward)
        except ValueError:
            await self.message.answer(
                f'`{escape_md(task_reward)}` is invalid value\\.',
                parse_mode=ParseModes.MARKDOWN_V2,
                reply_markup=get_reply_for_cancel_question('Cancel reward editing'),
            )
            return

        user_manager = UserManager(user=self.message.from_user)
        task_manager = TaskManager(user=self.message.from_user)

        task = await task_manager.get_task(task_id)

        await task_manager.update_task_reward(task=task, new_reward=task_reward)
        await user_manager.clear_waiting_of_answer()
        await self.message.reply('You successfully updated the task reward!')


class EditTask(BaseHandler):
    name = CallbackCommands.EDIT_TASK
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, task_id: str) -> None:
        task_id = int(task_id)
        task_manager = TaskManager(user=self.message.from_user)
        task = await task_manager.get_task(task_id)
        category_name = task.category.name if task.category else ''

        await self.message.answer(
            (
                f'*Name:* `{escape_md(task.name)}`\n'
                f'*Category:* `{escape_md(category_name)}`\n'
                f'*Reward:* `{escape_md(task.str_reward)}`\n\n'
                f'What do you want to do with this task?'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        f'{emojize(":pencil:")} Change name',
                        callback_data=f'{CallbackCommands.CHANGE_TASK_NAME} {task.id}',
                    ),
                    InlineKeyboardButton(
                        f'{emojize(":file_folder:")} Change category',
                        callback_data=f'{CallbackCommands.CHANGE_TASK_CATEGORY} {task.id}',
                    ),
                ],
                [
                    InlineKeyboardButton(
                        f'{emojize(":coin:")} Change reward',
                        callback_data=f'{CallbackCommands.CHANGE_TASK_REWARD} {task.id}',
                    ),
                    InlineKeyboardButton(
                        f'{emojize(":up-down_arrow:")} Change position',
                        callback_data=f'{CallbackCommands.CHANGE_TASK_POSITION} {task.id}',
                    ),
                ],
                [

                    InlineKeyboardButton(
                        f'{emojize(":wastebasket:")} Delete',
                        callback_data=f'{CallbackCommands.DELETE_TASK} {task.id}',
                    ),
                ],
            ]),
        )


class DeleteTask(BaseHandler):
    name = CallbackCommands.DELETE_TASK
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, task_id: str) -> None:
        task_id = int(task_id)

        task_manager = TaskManager(user=self.message.from_user)

        await task_manager.delete_task(task_id=task_id)
        await self.message.answer(
            f'Successfully removed {emojize(":thumbs_up:")}\n'
            f'(Your work logs are saved, don\'t worry.)'
        )


class DeleteCategory(BaseHandler):
    name = CallbackCommands.DELETE_CATEGORY
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, category_id: str) -> None:
        category_id = int(category_id)

        category_manager = CategoryManager(user=self.message.from_user)

        await category_manager.delete_category(category_id=category_id)
        await self.message.answer(
            f'Successfully removed {emojize(":thumbs_up:")}\n'
            f'(Your tasks and work logs are saved, don\'t worry.)'
        )


class EditCategory(BaseHandler):
    name = CallbackCommands.EDIT_CATEGORY
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, category_id: str) -> None:
        category_id = int(category_id)
        category_manager = CategoryManager(user=self.message.from_user)
        category = await category_manager.get_category(category_id)

        await self.message.answer(
            (
                f'*Name:* `{escape_md(category.name)}`\n\n'
                f'What do you want to do with this category?'
            ),
            parse_mode=ParseModes.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    f'{emojize(":pencil:")} Change name',
                    callback_data=f'{CallbackCommands.CHANGE_CATEGORY_NAME} {category.id}',
                ),
            ]]),
        )


class ShowStats(BaseHandler):
    name = BotCommand.SHOW_STATS
    type = HandlerTypes.MESSAGE

    async def handle(self) -> None:
        task_manager = TaskManager(user=self.message.from_user)
        work_date = self.message.from_user.get_selected_work_date()
        dates = tuple(
            work_date - datetime.timedelta(days=i)
            for i in reversed(range(7))
        )

        work_logs_stats = WorkLogsStats()
        await work_logs_stats.set_data_from_db_for_period(
            date_range=(dates[0], dates[-1],),
            for_user=self.message.from_user,
        )

        answer = f'*Date: `{work_date.isoformat()}`*\n\n'
        answer += f'*Stats for the last 7 days:*\n'

        for i, date in enumerate(dates, 1):
            n = emojize(f':keycap_{i}:')
            week_average = work_logs_stats.get_week_average(date)
            answer += f'{n} *`{date.isoformat()}`:* `{week_average}` {get_emojize_for_score(week_average)}\n'

        work_logs = await task_manager.get_work_logs()

        if work_logs:
            answer += f'\n*Your finished tasks:*\n'

            for work_log in work_logs:
                if work_log.reward > 0:
                    reward = f'+{work_log.reward}'
                else:
                    reward = str(work_log.reward)

                answer += f'`{reward}` — {escape_md(work_log.showed_name)}\n'

        day_score = work_logs_stats.get_day_score(work_date)
        week_average = work_logs_stats.get_week_average(work_date)

        answer += f'\n{get_day_performance_info(day_score=day_score, week_average=week_average)}'

        await self.message.answer(
            answer,
            parse_mode=ParseModes.MARKDOWN_V2,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            f'{emojize(":spiral_calendar:")} Calendar heatmap',
                            callback_data=CallbackCommands.SHOW_CALENDAR_HEATMAP,
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            f'{emojize(":broom:")} Check & Clean',
                            callback_data=CallbackCommands.SHOW_FINISHED_TASKS,
                        ),
                        InlineKeyboardButton(
                            f'{emojize(":light_bulb:")} What to do',
                            callback_data=CallbackCommands.SHOW_OLD_TASKS,
                        ),
                    ],
                ],
            ),
        )


class ShowCalendarHeatmap(BaseHandler):
    name = CallbackCommands.SHOW_CALENDAR_HEATMAP
    type = HandlerTypes.CALLBACK_QUERY

    @with_throttling(datetime.timedelta(hours=1), count=5)
    async def handle(self) -> None:
        year = self.message.from_user.get_selected_work_date().year
        work_logs_stats = WorkLogsStats()
        file_name, buffer = await work_logs_stats.generate_year_plot(year=year, for_user=self.message.from_user)

        await self.message.answer_document(
            TelegramInputFile(buffer, filename=file_name),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[
                    InlineKeyboardButton(
                        f'{emojize(":magnifying_glass_tilted_left:")} Show more',
                        callback_data=CallbackCommands.SHOW_DETAILED_STATISTICS,
                    ),
                ]],
            )
        )


class ShowDetailedStats(BaseHandler):
    name = CallbackCommands.SHOW_DETAILED_STATISTICS
    type = HandlerTypes.CALLBACK_QUERY

    @with_throttling(datetime.timedelta(hours=1), count=5)
    async def handle(self) -> None:
        work_logs_stats = WorkLogsStats()
        years_with_work_logs = (await work_logs_stats.get_years_with_work_logs(for_user=self.message.from_user))[:-1]

        if not years_with_work_logs:
            await self.message.answer_document(f'No more data {emojize(":sad_but_relieved_face:")}')
            return

        for year in reversed(years_with_work_logs):
            file_name, buffer = await work_logs_stats.generate_year_plot(year=year, for_user=self.message.from_user)
            work_logs_stats.reset()
            await self.message.answer_document(TelegramInputFile(buffer, filename=file_name))


class DeleteWorkLog(BaseHandler):
    name = CallbackCommands.DELETE_WORK_LOG
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self, work_log_id: str) -> None:
        work_log_id = int(work_log_id)

        task_manager = TaskManager(user=self.message.from_user)

        try:
            result = await task_manager.delete_work_log(work_log_id)
        except ValidationError as e:
            await self.message.answer_error(e)
        else:
            await self.message.answer(f'Successfully removed {emojize(":thumbs_up:")}')

            day_bonus = result['day_bonus']

            if day_bonus != 0:
                await self.message.answer(
                    get_text_for_new_day_bonus(day_bonus),
                    parse_mode=ParseModes.MARKDOWN_V2,
                )


class ImportWorkLogs(BaseHandler):
    name = CallbackCommands.IMPORT_WORK_LOGS
    type = HandlerTypes.CALLBACK_QUERY

    async def handle(self) -> None:
        task_manager = TaskManager(user=self.message.from_user)
        user_manager = UserManager(user=self.message.from_user)

        await self.message.answer('Example:')
        await self.message.answer_document(
            TelegramInputFile(io.StringIO(task_manager.get_template_for_import_task_logs()), filename='example.json'),
        )
        await user_manager.wait_answer_for(constants.QuestionTypes.FILE_WITH_WORK_LOGS)
        await self.message.answer(
            (
                f'{emojize(":warning:")} It will replace data for provided dates.\n\n'
                f'Upload your JSON file:'
            ),
            reply_markup=get_reply_for_cancel_question(),
        )


class ExportData(BaseHandler):
    name = CallbackCommands.EXPORT_DATA
    type = HandlerTypes.CALLBACK_QUERY

    @with_throttling(datetime.timedelta(hours=3))
    async def handle(self) -> None:
        task_manager = TaskManager(user=self.message.from_user)
        exported_data = await task_manager.export_data()

        for file_name, data in exported_data.items():
            await self.message.answer_document(
                TelegramInputFile(io.StringIO(data), filename=file_name),
            )


class AnswerWithWorkLogs(BaseHandler):
    name = QuestionTypes.FILE_WITH_WORK_LOGS
    type = HandlerTypes.FILE_ANSWER

    @with_throttling(datetime.timedelta(days=1), count=3)
    async def handle(self, document: TelegramDocument) -> None:
        task_manager = TaskManager(user=self.message.from_user)
        user_manager = UserManager(user=self.message.from_user)

        if document.file_size > 1024 * 1024:
            await self.message.answer(
                'Your file is too large (> 1 Mb).',
                reply_markup=get_reply_for_cancel_question(),
            )
            return

        if document.mime_type != 'application/json':
            await self.message.answer(
                'You need to upload a JSON file.',
                reply_markup=get_reply_for_cancel_question(),
            )
            return

        buffer = io.BytesIO()
        await document.download(buffer)

        try:
            data = json.load(buffer)
        except json.JSONDecodeError:
            await self.message.answer(
                'JSON is invalid.',
                reply_markup=get_reply_for_cancel_question(),
            )
            return

        try:
            await task_manager.import_work_logs(data)
        except ValidationError as e:
            await self.message.answer_error(
                e,
                reply_markup=get_reply_for_cancel_question(),
            )
            return
        except Exception as e:
            logging.exception(e)
            await self.message.answer(
                'Something wrong. Check your data.',
                reply_markup=get_reply_for_cancel_question(),
            )
        finally:
            await user_manager.clear_waiting_of_answer()

        await self.message.reply(
            f'Successfully saved {emojize(":thumbs_up:")}',
        )
