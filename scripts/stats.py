import asyncio
import datetime
import json
import logging
import sys


sys.path.append('/app')

from app import models
from app.models.utils import get_count, init_db


async def main() -> None:
    logging.info('Initialization DB...')
    await init_db()

    print(json.dumps(
        {
            'users': await models.User.all().count(),
            'active_users': await get_count(models.WorkLog.filter(
                date__gte=datetime.date.today() - datetime.timedelta(days=7),
            ).distinct().values(
                'owner_id',
            )),
        },
        indent=2,
    ))


asyncio.run(main())
