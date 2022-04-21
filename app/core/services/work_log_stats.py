import datetime
import io
import typing

import calmap
import matplotlib.pyplot as plt
import pandas as pd
from mpl_toolkits.axes_grid1 import make_axes_locatable
from tortoise.functions import Sum

from ... import models
from .. import constants
from ...models.utils import get_first


class WorkLogsStats:
    _day_score_map: dict[datetime.date, int]

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._day_score_map = {}

    @classmethod
    async def get_years_with_work_logs(cls, *, for_user: models.User) -> tuple[int, ...]:
        first_work_date = await cls._get_first_work_date(for_user=for_user)

        current_year = for_user.get_selected_work_date().year

        if not first_work_date:
            return (current_year,)

        first_work_year = first_work_date.year

        if first_work_year > current_year:
            return (current_year,)

        return tuple(range(first_work_year, current_year + 1))

    async def set_data_from_db_for_date(self, *,
                                        date: datetime.date,
                                        for_user: models.User) -> None:
        await self.set_data_from_db_for_period(
            date_range=(date, date,),
            for_user=for_user,
        )

    async def set_data_from_db_for_period(self, *,
                                          date_range: tuple[datetime.date, ...],
                                          for_user: models.User) -> None:
        stats = tuple(await models.WorkLog.filter(
            owner=for_user,
            date__gte=date_range[0] - datetime.timedelta(days=6),
            date__lte=date_range[1],
        ).group_by(
            'date',
        ).annotate(
            day_score=Sum('reward'),
        ).values_list(
            'date',
            'day_score',
        ))

        for date, day_score in stats:
            self.add_day_score(score=day_score, date=date)

    async def get_year_plot(self, *, year: int, for_user: models.User) -> tuple[str, io.BytesIO]:
        selected_work_date = for_user.get_selected_work_date()
        first_work_date = await self._get_first_work_date(for_user=for_user)
        start_year = datetime.date(year=year, month=1, day=1)

        if first_work_date:
            start_date = max(first_work_date, start_year)
        else:
            start_date = start_year

        if start_date <= selected_work_date:
            await self.set_data_from_db_for_period(
                date_range=(start_date, selected_work_date,),
                for_user=for_user,
            )

        raw_data = {}
        date = start_date
        one_day = datetime.timedelta(days=1)

        while date <= selected_work_date:
            value = self.get_day_amount(date)

            if value > constants.TARGET_NUMBER:
                value = constants.TARGET_NUMBER
            elif value < 0:
                value = 0

            raw_data[date] = value

            date += one_day

        data = pd.Series(raw_data)
        data.index = pd.to_datetime(data.index.values)

        fig, ax = plt.subplots(figsize=(16, 4,))
        cax = calmap.yearplot(
            data,
            ax=ax,
            year=start_date.year,
            cmap='RdPu',
            linewidth=1,
            linecolor=None,
            vmin=0,
            vmax=constants.TARGET_NUMBER,
            fillcolor=(1, 1, 1, 0.1,),
        )

        name = f'Your productivity for {year}'
        fig.suptitle(name, y=0.8, fontsize=20)

        divider = make_axes_locatable(cax)
        lcax = divider.append_axes('right', size='2%', pad=0.5)
        fig.colorbar(cax.get_children()[1], cax=lcax)

        buffer = io.BytesIO()
        fig.savefig(buffer, format='png')
        buffer.seek(0)

        fig.clear()
        plt.close(fig)

        return f'{name}.png', buffer

    def add_day_score(self, *, score: int, date: datetime.date) -> None:
        if date not in self._day_score_map:
            self._day_score_map[date] = 0

        self._day_score_map[date] += score

    def get_day_score(self, for_date: datetime.date) -> int:
        return self._day_score_map.get(for_date, 0)

    def get_day_amount(self, for_date: datetime.date) -> int:
        return sum(
            self._day_score_map.get(for_date - datetime.timedelta(days=i), 0)
            for i in range(7)
        ) // 7

    @staticmethod
    async def _get_first_work_date(*, for_user: models.User) -> typing.Optional[datetime.date]:
        return await get_first(models.WorkLog.filter(
            owner=for_user,
        ).order_by(
            'date',
        ).values_list(
            'date',
            flat=True,
        ))
