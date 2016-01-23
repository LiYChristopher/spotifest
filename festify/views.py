from festify import festify
from flask import render_template, url_for
import requests
import spotipy
import spotipy.util


@festify.route('/login')
def oauth_login():
	'''
	renders 'login.html'

	GET: A page that prompts user to submit login details,
	sign in directly with Spotify credentials

	POST: If login is valid, redirect to url_for('home'), else
	flash an error -- "Your spotiy credentials are invalid."
	'''
	with open('credentials.txt') as cred:
		CLIENT_ID = str(cred.readline().split('>')[1]).replace('\n', '')
		CLIENT_SECRET = str(cred.readline().split('>')[1]).replace('\n', '')
		REDIRECT_URI = str(cred.readline().split('>')[1]).replace('\n', '')

	# utility of spotipy.oauth2.SpotifyOauth
	# let's us store everything in one container, as well as gives us the authorize URL.
	oauth = spotipy.oauth2.SpotifyOAuth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
										redirect_uri=REDIRECT_URI, scope='playlist-modify-public')

	# but since the above doesn't build the actual URL for us, we have to do it ourselves
	# through requests library.
	payload = {'client_id': oauth.client_id, 'client_secret': oauth.client_secret,
				'response_type': 'code', 'redirect_uri': oauth.redirect_uri,
				'scope': oauth.scope}

	# pass the URL through as a *arg to render template
	r = requests.get(oauth.OAUTH_AUTHORIZE_URL, params=payload)
	return render_template('login.html', oauth=r.url)


@festify.route('/')
@festify.route('/home')
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
	return 'Hello world.'


@festify.route('/generate')
def generate():
	'''
	renders 'generate.html'

	GET: The respective pyechonest/spotipy helper(s) will be called,
	and produce a table (iter obj) of artists/and or songs

	POST: Take form info (which should now be a collection of songs/artists),
	and feed it into the pyechonest helper that will create a catalog,
	which feeds into a playlist.

	return redirect(url_for('results.html')) with newly formed playlist.
	'''


@festify.route('/results')
def results():
	'''
	renders 'login.html'

	GET: Return 404, because there's no playlist that has been processed.

	POST: Displays playlist (list object produced by form from the home route)results as a table
	at the bottom of the document is a button that allows user to save to their account, open in
	the desktop player. (see spotipy API)
	'''

@festify.errorhandler(404)
def not_found(e):
	'''
	renders '404.html'
	'''
	return
