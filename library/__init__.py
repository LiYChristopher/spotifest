# creates the app and can include a config.py
from flask import Flask
from celery import Celery
from flask.ext.login import LoginManager
from flask.ext.mysql import MySQL
import os


def create_app(config=None, app_name=None, blueprints=None):
    app = Flask(__name__)
    return app


def find_config(filename):
    config_fname = filename
    app_root = os.getcwd().split('library')[0]
    for r, d, f in os.walk(app_root):
        if config_fname in f:
            return os.path.join(app_root, config_fname)
    raise IOError("Config file name at '{}' could not be found.".format(config_fname))

path = find_config('config.py')
os.environ['APP_CONFIG'] = path

app = create_app()
app.config.from_envvar('APP_CONFIG')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

login_manager = LoginManager()
login_manager.init_app(app)

mysql = MySQL()

mysql.init_app(app)

from . import auth
