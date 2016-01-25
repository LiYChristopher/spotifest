from library.app import create_app
from flask.ext.login import LoginManager

app = create_app()
login_manager = LoginManager()
login_manager.init_app(app)

from library import auth
# import library.festify