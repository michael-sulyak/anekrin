import asyncio
import logging
import typing

from aiogram.types import (
    Update as TelegramUpdate,
)
from emoji.core import emojize

from .tasks import TaskManager
from .users import UserManager
from ..base import BaseMessage, Message
from ..constants import BotCommand, CallbackCommands, QuestionTypes
from ..handlers.base import BaseHandler
from ..handlers.constants import HandlerTypes, MessageContentTypes
from ..handlers.implementation import (
    common as handlers_for_common_usage, tasks as handlers_for_tasks, users as handlers_for_users,
)
from ..utils import send_not_found, send_not_found_for_question


class TelegramMessageHandler:
    available_handler_classes: tuple[typing.Type[BaseHandler], ...] = (
        handlers_for_tasks.ShowTasks,
        handlers_for_tasks.ShowTasksInCategory,
        handlers_for_tasks.ShowFinishedTask,
        handlers_for_tasks.CompleteTask,
        handlers_for_tasks.CreateTask,
        handlers_for_tasks.EditTask,
        handlers_for_tasks.DeleteTask,
        handlers_for_tasks.CreateCategory,
        handlers_for_tasks.DeleteCategory,
        handlers_for_tasks.ChangeCategoryName,
        handlers_for_tasks.ChangeTaskCategory,
        handlers_for_tasks.SetTaskCategory,
        handlers_for_tasks.EditCategory,
        handlers_for_tasks.ShowStats,
        handlers_for_tasks.DeleteWorkLog,
        handlers_for_tasks.AnswerWithNameForNewTask,
        handlers_for_tasks.AnswerWithNameForNewCategory,
        handlers_for_tasks.AnswerWithNewNameForCategory,
        handlers_for_tasks.AnswerWithNewTaskReward,
        handlers_for_tasks.AnswerWithNewNameForTask,
        handlers_for_tasks.ChangeTaskReward,
        handlers_for_tasks.ChangeTaskName,
        handlers_for_tasks.RewriteAllTasks,
        handlers_for_tasks.AnswerWithTaskInfo,
        handlers_for_tasks.ShowOldTasks,
        handlers_for_tasks.ShowCalendarHeatmap,
        handlers_for_tasks.ImportWorkLogs,
        handlers_for_tasks.AnswerWithWorkLogs,
        handlers_for_tasks.ExportData,
        handlers_for_tasks.ShowDetailedStats,

        handlers_for_users.ShowSettings,
        handlers_for_users.ChooseDate,
        handlers_for_users.UpdateTZ,
        handlers_for_users.AnswerWithTZ,
        handlers_for_users.ResetWorkDate,
        handlers_for_users.SelectYesterday,
        handlers_for_users.SetWorkDate,

        handlers_for_common_usage.Start,
        handlers_for_common_usage.Help,
        handlers_for_common_usage.CancelQuestion,
    )
    handler_classes_map: typing.Dict[str, typing.Dict[str, typing.Type[BaseHandler]]]
    _message_class: typing.Type[BaseMessage]
    _tasks_map: typing.Dict[int, asyncio.Task]

    def __init__(self, *, message_class: typing.Type[BaseMessage] = Message) -> None:
        self._message_class = message_class
        self._fill_handler_classes_map()
        self._tasks_map = {}

    async def process_update(self,
                             telegram_update: TelegramUpdate, *,
                             immediately: bool = False) -> None:
        try:
            telegram_user_id = self._extract_telegram_user_id(telegram_update)
        except Exception as e:
            logging.exception(e)
            return

        if not telegram_user_id:
            return

        if immediately:
            await self._process_update_with_awaiting(telegram_update)
        else:
            wait_for = self._tasks_map.get(telegram_user_id)

            self._tasks_map[telegram_user_id] = asyncio.create_task(
                self._process_update_with_awaiting(telegram_update, wait_for=wait_for),
            )

    async def _process_update_with_awaiting(self,
                                            telegram_update: TelegramUpdate, *,
                                            wait_for: typing.Optional[asyncio.Task] = None) -> None:
        try:
            if wait_for is not None:
                await wait_for

            await self._process_update(telegram_update)
        except Exception as e:
            logging.exception(e)

    async def _process_update(self, telegram_update: TelegramUpdate) -> None:
        callback_query = None
        command_args = ()

        if telegram_update.message:
            if telegram_update.message.content_type == MessageContentTypes.MESSAGE_AUTO_DELETE_TIMER_CHANGED:
                return

            telegram_message = telegram_update.message
            user, user_is_created = await UserManager.get_user_by_telegram_user(telegram_message.from_user)
            message = self._message_class(from_user=user, telegram_message=telegram_message)

            if user.wait_answer_for:
                command_name, *command_args = user.wait_answer_for.split(' ')

                if telegram_message.document:
                    handler_type = HandlerTypes.FILE_ANSWER
                    command_args = (telegram_message.document, *command_args,)
                else:
                    handler_type = HandlerTypes.ANSWER
                    command_args = (telegram_message.text, *command_args,)
            else:
                command_name = telegram_message.text
                handler_type = HandlerTypes.MESSAGE
        elif telegram_update.callback_query:
            callback_query = telegram_update.callback_query
            command_name, *command_args = callback_query.data.split(' ')
            user, user_is_created = await UserManager.get_user_by_telegram_user(callback_query.from_user)
            message = self._message_class(from_user=user, telegram_message=callback_query.message)
            handler_type = HandlerTypes.CALLBACK_QUERY
        else:
            return

        if handler_type == HandlerTypes.CALLBACK_QUERY and user.wait_answer_for:
            await UserManager(user=user).clear_waiting_of_answer()

        try:
            handler_class = self.handler_classes_map[handler_type][command_name]
        except KeyError:
            if handler_type in (HandlerTypes.ANSWER, HandlerTypes.FILE_ANSWER,):
                await UserManager(user=user).clear_waiting_of_answer()
                await send_not_found_for_question(message)
            else:
                await send_not_found(message)

            return

        try:
            await handler_class(message=message).handle(*command_args)
        except Exception as e:
            logging.exception(e)
            await message.answer(f'Unexpected error {emojize(":anxious_face_with_sweat:")}')

        if handler_type == HandlerTypes.CALLBACK_QUERY:
            await callback_query.answer()

        if user_is_created:
            await TaskManager(user=user).create_samples()
            await message.answer('I created samples for your. You can delete them.')

    @staticmethod
    def _extract_telegram_user_id(telegram_update: TelegramUpdate) -> typing.Optional[int]:
        if telegram_update.message:
            return telegram_update.message.from_user.id
        elif telegram_update.callback_query:
            return telegram_update.callback_query.from_user.id
        else:
            return None

    def _fill_handler_classes_map(self) -> None:
        self.handler_classes_map = {}

        handler_types_map: typing.Dict[str, set] = {  # NOQA
            HandlerTypes.MESSAGE: BotCommand.ALL,
            HandlerTypes.CALLBACK_QUERY: CallbackCommands.ALL,
            HandlerTypes.ANSWER: QuestionTypes.ALL,
            HandlerTypes.FILE_ANSWER: QuestionTypes.ALL,
        }

        for handler_class in self.available_handler_classes:
            if handler_class.type not in self.handler_classes_map:
                self.handler_classes_map[handler_class.type] = {}

            if handler_class.name in self.handler_classes_map[handler_class.type]:
                raise RuntimeError(f'"{handler_class.type}.{handler_class.name}" is already added.')

            if handler_class.name not in handler_types_map[handler_class.type]:
                raise RuntimeError(f'"{handler_class.type}.{handler_class.name}" is not found.')

            self.handler_classes_map[handler_class.type][handler_class.name] = handler_class

        for handler_type, handler_values in handler_types_map.items():
            for handler_value in handler_values:
                if handler_value in self.handler_classes_map[handler_type]:
                    continue

                if (
                        handler_type in HandlerTypes.ANSWER
                        and handler_value in self.handler_classes_map[HandlerTypes.FILE_ANSWER]
                ):
                    continue

                if (
                        handler_type in HandlerTypes.FILE_ANSWER
                        and handler_value in self.handler_classes_map[HandlerTypes.ANSWER]
                ):
                    continue

                raise RuntimeError(f'Handler for "{handler_type}.{handler_value}" is not found.')
