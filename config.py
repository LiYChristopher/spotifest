#config.py
SECRET_KEY = 'this_is_a_secret'
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_RESULT_EXPIRES = 3600
IS_ASYNC = False

class BaseConfig(object):

	with open('credentials.txt', 'r') as cred:
		CLIENT_ID = str(cred.readline().split('>')[1].replace('\n', ''))
		CLIENT_SECRET = str(cred.readline().split('>')[1].replace('\n', ''))
		REDIRECT_URI = str(cred.readline().split('>')[1].replace('\n', ''))

	if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
		raise Exception('Credentials could not be configured. See credentials.txt.')
