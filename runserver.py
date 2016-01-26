from library.run import app

app.config.from_object('config')
app.run(debug=True)
