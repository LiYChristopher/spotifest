#creates the app and can include a config.py
from flask import Flask
from flask.ext.login import LoginManager

def create_app(config=None, app_name=None, blueprints=None):
    app = Flask(__name__)
    return app

app = create_app()

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)