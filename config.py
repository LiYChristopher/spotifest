# config.py
from datetime import timedelta

SECRET_KEY = 'this_is_a_secret'

# Celery config
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_RESULT_EXPIRES = 3600
CELERYBEAT_SCHEDULE = {
    'add-every-hour': {
        'task': 'routine_deletion_expired',
        'schedule': timedelta(minutes=60)
    },
}
IS_ASYNC = True

class BaseConfig(object):

    with open('credentials.txt', 'r') as cred:
        CLIENT_ID = str(cred.readline().split('>')[1].replace('\n', ''))
        CLIENT_SECRET = str(cred.readline().split('>')[1].replace('\n', ''))
        REDIRECT_URI = str(cred.readline().split('>')[1].replace('\n', ''))
        ECHONEST_API_KEY = str(cred.readline().split('>')[1].replace('\n', ''))
        MYSQL_PASSWORD = str(cred.readline().split('>')[1].replace('\n', ''))

    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        raise Exception('Credentials could not be configured. See credentials.txt.')

MYSQL_DATABASE_USER = 'root'
MYSQL_DATABASE_DB = 'festify'
MYSQL_DATABASE_HOST = BaseConfig.MYSQL_PASSWORD
MYSQL_DATABASE_PASSWORD = 'uberschall'
