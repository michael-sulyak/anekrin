import os


DATABASE_NAME = 'anekrin'
DATABASE_USER = os.environ['POSTGRES_USER']
DATABASE_PASSWORD = os.environ['POSTGRES_PASSWORD']
DATABASE_HOST = os.environ['POSTGRES_HOST']
DATABASE_PORT = os.environ['POSTGRES_PORT']
DATABASE_URL = f'postgres://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}'

TORTOISE_ORM = {
    'connections': {
        'default': DATABASE_URL,
    },
    'apps': {
        'models': {
            'models': (
                'app.models',
                'aerich.models',
            ),
            'default_connection': 'default',
        },
    },
}

TELEGRAM_API_TOKEN = os.environ['TELEGRAM_API_TOKEN']
SENTRY_DSN = os.environ['SENTRY_DSN']
TELEHOOKS_MQ_URL = os.environ['TELEHOOKS_MQ_URL']
TELEHOOKS_MQ_QUEUE_NAME = os.environ['TELEHOOKS_MQ_QUEUE_NAME']
