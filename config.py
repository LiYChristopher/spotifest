# config.py
from datetime import timedelta
import os


DEBUG = False
SECRET_KEY = 'this_is_a_secret'
# path = os.path.abspath('credentials.txt')
# os.chdir(path[:-15])

#def full_path(file):
#    path = os.path.dirname(os.path.abspath(__file__))
#    return os.path.join(path, file)

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

CACHE_TYPE = 'redis'
CACHE_REDIS_HOST = 'localhost'
CACHE_REDIS_PORT = 6379


class BaseConfig(object):

    def file_path(file):
        path = os.path.dirname(os.path.abspath(__file__))
        joined = os.path.join(path, file)
        return os.path.join(path, file)

    with open(file_path('credentials.txt'), 'r') as cred:
        CLIENT_ID = str(cred.readline().split('>')[1].replace('\n', ''))
        CLIENT_SECRET = str(cred.readline().split('>')[1].replace('\n', ''))
        REDIRECT_URI = str(cred.readline().split('>')[1].replace('\n', ''))
        ECHONEST_API_KEY = str(cred.readline().split('>')[1].replace('\n', ''))
        MYSQL_PASSWORD = str(cred.readline().split('>')[1].replace('\n', ''))
        APP_LOG_PATH = file_path('app_errors.log')	

    if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
        raise Exception('Credentials could not be configured. See credentials.txt.')

APP_LOG_PATH = BaseConfig.APP_LOG_PATH

MYSQL_DATABASE_USER = 'root'
MYSQL_DATABASE_DB = 'spotifest2'
MYSQL_DATABASE_HOST = 'localhost'
MYSQL_DATABASE_PASSWORD = BaseConfig.MYSQL_PASSWORD


