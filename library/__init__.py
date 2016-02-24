import eventlet
import redis
import celery

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
print os.getcwd()

celery = celery.Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

login_manager = LoginManager()
login_manager.init_app(app)

mysql = MySQL()

# mysql configurations

mysql.init_app(app)

from . import auth
