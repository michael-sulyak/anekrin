import datetime
import zoneinfo

from tortoise import fields
from tortoise.contrib.postgres import indexes
from tortoise.models import Model

from app.core import constants
from app.core.constants import WorkLogTypes
from app.models.contrib import UniqueTogether


class User(Model):
    id = fields.BigIntField(
        pk=True,
    )
    telegram_user_id = fields.BigIntField(
        unique=True,
    )
    wait_answer_for = fields.TextField(
        null=True,
    )
    selected_work_date = fields.DateField(
        null=True,
    )
    timezone = fields.CharField(
        max_length=20,
        default=zoneinfo.ZoneInfo('UTC').key,
    )

    def __str__(self) -> str:
        return f'User #{self.id}'

    def get_selected_work_date(self) -> datetime.date:
        if self.selected_work_date:
            return self.selected_work_date

        return self.get_today_in_user_tz()

    def get_today_in_user_tz(self) -> datetime.date:
        now = datetime.datetime.now().astimezone()
        return now.astimezone(zoneinfo.ZoneInfo(self.timezone)).date()


class Category(Model):
    id = fields.BigIntField(
        pk=True,
    )
    name = fields.TextField()
    owner: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name='models.User',
        related_name='categories',
        index=True,
    )

    class Meta:
        indexes = (
            UniqueTogether(fields={'owner_id', 'name'}, is_deferrable_initially_immediate=True),
        )


class Task(Model):
    id = fields.BigIntField(
        pk=True,
    )
    name = fields.TextField()
    owner: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name='models.User',
        related_name='tasks',
        index=True,
    )
    category: fields.ForeignKeyRelation[Category] = fields.ForeignKeyField(
        model_name='models.Category',
        related_name='tasks',
        on_delete=fields.SET_NULL,
        null=True,
        index=True,
    )
    position = fields.IntField()
    reward = fields.IntField()
    created_at = fields.DatetimeField(
        auto_now_add=True,
    )

    def __str__(self) -> str:
        return f'Task #{self.id}'

    @property
    def str_reward(self) -> str:
        if self.reward > 0:
            return f'+{self.reward}'
        else:
            return str(self.reward)

    class Meta:
        indexes = (
            UniqueTogether(fields={'owner_id', 'position'}, is_deferrable_initially_immediate=True),
            UniqueTogether(fields={'owner_id', 'name'}, is_deferrable_initially_immediate=True),
        )


class WorkLog(Model):
    id = fields.BigIntField(
        pk=True,
    )
    type = fields.CharField(
        max_length=20,
        default=WorkLogTypes.USER_WORK,
    )
    task: fields.ForeignKeyRelation[Task] = fields.ForeignKeyField(
        model_name='models.Task',
        related_name='work_logs',
        on_delete=fields.SET_NULL,
        null=True,
        index=True,
    )
    name = fields.TextField()
    date = fields.DateField()
    owner: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        model_name='models.User',
        related_name='work_logs',
        index=True,
    )
    reward = fields.IntField()

    def __str__(self) -> str:
        return f'WorkLog #{self.id}'

    class Meta:
        indexes = (
            indexes.BrinIndex(fields={'owner_id', 'date'}),
            indexes.BrinIndex(fields={'task_id', 'date'}),
        )

    @property
    def showed_name(self) -> str:
        if self.type == constants.WorkLogTypes.BONUS:
            return constants.BONUS_TASK_NAME
        else:
            return self.name
