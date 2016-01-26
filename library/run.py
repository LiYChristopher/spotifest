#run.py

from library.app import app
from library import auth

from flask.ext.login import LoginManager

login_manager = LoginManager()
login_manager.init_app(app)

