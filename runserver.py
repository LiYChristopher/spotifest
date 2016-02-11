from library import app

print app.__dict__
print app.url_map


app.run(debug=True)
