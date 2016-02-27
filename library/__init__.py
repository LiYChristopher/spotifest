import eventlet
import redis
import celery
import logging

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.mysql import MySQL
import os

# enable greenthreads
eventlet.monkey_patch()


def create_app(config=None, app_name=None, blueprints=None):
    app = Flask(__name__)
    return app


app = create_app()
app.config.from_object('config')

# logging setup
if not app.debug is True:
    file_loc = os.path.join(os.getcwd(), 'app_errors.log')
    file_handler = logging.FileHandler('app_errors.log')
    file_handler.setLevel(logging.WARNING)
    formatter = logging.Formatter('%(asctime)s -- %(levelname)s'
                                  '< line %(lineno)d %(module)s.%(funcName)s >: %(message)s')
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

# celery setup
celery = celery.Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

# flask-login setup
login_manager = LoginManager()
login_manager.init_app(app)

# mysql setup
mysql = MySQL()
mysql.init_app(app)

from . import auth
