from app import app
from flask import render_template


@app.route('/login')
def oauth_login():
	''' 
	renders 'login.html'

	GET: A page that prompts user to submit login details,
	sign in directly with Spotify credentials

	POST: If login is valid, redirect to url_for('home'), else
	flash an error -- "Your spotiy credentials are invalid." 
	'''
	return


@app.route('/home')
def home():
	'''
	renders 'home.html'

	includes nav-bar for different 'build' options
	(headliners? personal preferences? group preferences?
	these will end up being separate views.)

	GET: A page with multple buttons:
		- Get my playlists
		- Get my recently listened to Artists
		- Get my saved songs
		- more?
	Clicking on each button runs the respective spotipy helper function
	that will extract this info for us

	There will also be a panel for parameter settings

	POST: Take form info (which should now be a collection of songs/artists), 
	and feed it into the pyechonest helper that will create a catalog, 
	which feeds into a playlist.
	return redirect(url_for('results.html')) with newly formed playlist.
	'''
	return


@app.route('/generate/single')
def generate_single():
	'''
	renders 'generate.html'

	GET: The respective pyechonest/spotipy helper(s) will be called, 
	and produce a table (iter obj) of artists/and or songs  

	POST: Take form info (which should now be a collection of songs/artists), 
	and feed it into the pyechonest helper that will create a catalog, 
	which feeds into a playlist.
	return redirect(url_for('results.html')) with newly formed playlist.
	'''


@app.route('/generate/group')
def generate_single():
	'''
	renders 'generate.html'

	GET: The respective pyechonest/spotipy helper(s) will be called, 
	and produce a table (iter obj) of artists/and or songs  

	POST: Take form info (which should now be a collection of songs/artists), 
	and feed it into the pyechonest helper that will create a catalog, 
	which feeds into a playlist.
	return redirect(url_for('results.html')) with newly formed playlist.
	'''


@app.route('/generate/group')
def generate_single():
	'''
	renders 'generate.html'

	GET: The respective pyechonest/spotipy helper(s) will be called, 
	and produce a table (iter obj) of artists/and or songs  

	POST: Take form info (which should now be a collection of songs/artists), 
	and feed it into the pyechonest helper that will create a catalog, 
	which feeds into a playlist.
	return redirect(url_for('results.html')) with newly formed playlist.
	'''


@app.route('/results')
def results():
	'''
	renders 'login.html'

	GET: Return 404, because there's no playlist that has been processed.

	POST: Displays playlist (list object produced by form from the home route)results as a table
	at the bottom of the document is a button that allows user to save to their account, open in 
	the desktop player. (see spotipy API)
	'''

@app.errorhandler(404)
def not_found(e):
	'''
	renders '404.html'
	'''

