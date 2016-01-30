#creates the app and can include a config.py
from flask import Flask
from celery import Celery
from flask.ext.login import LoginManager
from flask.ext.mysql import MySQL

def create_app(config=None, app_name=None, blueprints=None):
    app = Flask(__name__)
    return app

app = create_app()
app.config.from_object('config')

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

login_manager = LoginManager()
login_manager.init_app(app)

mysql = MySQL()

# mysql configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'festify'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
