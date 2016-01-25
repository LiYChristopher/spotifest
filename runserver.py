from library import create_app
from library import app
from flask.ext.login import LoginManager


login_manager = LoginManager()
login_manager.init_app(app)

app.config.from_object('config')
app.run(debug=True)
