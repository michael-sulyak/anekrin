import datetime
import functools
import typing
from collections import defaultdict, deque

from emoji.core import emojize

from ...constants import ParseModes
from ....common.utils.datetimes import prettify_timedelta


def with_throttling(period: datetime.timedelta, *, count: int = 1) -> typing.Callable:
    def _decorator(method: typing.Callable) -> typing.Callable:
        if not hasattr(method, 'times_of_run_map'):
            method.times_of_run_map = defaultdict(deque)

        times_of_run_map = method.times_of_run_map  # NOQA

        @functools.wraps(method)
        async def _wrapper(self, *args, **kwargs) -> None:
            times_of_run = times_of_run_map[self.message.from_user.id]

            now = datetime.datetime.now()

            while len(times_of_run) >= count:
                diff = now - times_of_run[0]

                if diff > period:
                    times_of_run.popleft()
                else:
                    await self.message.answer(
                        (
                            f'{emojize(":warning:")} You have exceeded the request limit for this action\\.\n'
                            f'You need to wait *{" and ".join(prettify_timedelta(period - diff)[:2])}*\\.'
                        ),
                        parse_mode=ParseModes.MARKDOWN_V2,
                    )
                    return

            times_of_run.append(now)

            await method(self, *args, **kwargs)

        return _wrapper

    return _decorator
