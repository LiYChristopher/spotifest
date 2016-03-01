import eventlet
import redis
import celery
import logging

from flask import Flask
from flask.ext.login import LoginManager
from flask.ext.mysql import MySQL
import os
import sys

# enable greenthreads
eventlet.monkey_patch()


def create_app(config=None, app_name=None, blueprints=None):
    app = Flask(__name__)
    return app


app = create_app()
app.config.from_object('config')

# logging setup
if not app.debug is True:
    file_loc = app.config.get('APP_LOG_PATH')
    if not file_loc:
    	raise IOError("Please specify path for app_error.logs")
    file_handler = logging.FileHandler(file_loc)
    file_handler.setLevel(logging.INFO)
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
