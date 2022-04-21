import datetime


def prettify_timedelta(td: datetime.timedelta) -> list[str]:
    seconds = int(td.total_seconds())
    periods = (
        ('year', 60 * 60 * 24 * 365,),
        ('month', 60 * 60 * 24 * 30,),
        ('day', 60 * 60 * 24,),
        ('hour', 60 * 60,),
        ('minute', 60,),
        ('second', 1),
    )

    strings = []
    for period_name, period_seconds in periods:
        if seconds <= period_seconds:
            continue

        period_value, seconds = divmod(seconds, period_seconds)
        strings.append(f'{period_value} {period_name}{"s" if period_value > 1 else ""}')

    return strings
