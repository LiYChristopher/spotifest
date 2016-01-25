from library import create_app
from library import app

app.config.from_object('config')
app.run(debug=True)

print app.url_map