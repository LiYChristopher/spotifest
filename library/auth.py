from library import app
from library.app import create_app
from library.app import spotify_connect
from config import BaseConfig

from flask import render_template, request, redirect, url_for
from flask import session
import spotipy
import spotipy.util as util
import os
import requests


@app.route('/')
def auth_check():
    '''
    check if with baseconfig returns good
    if BaseConfig is True:
        return rendter_template('preferences.html')
    else:
        return login
    '''
    pass

@app.route('/login', methods=['POST', 'GET'])
def login():
    '''prompts user to login via OAuth2 through Spotify
    this shows up in index.html

    if current_user.is_authenticated():
        return redirect(url_for('choose_parameters'))

    form
    '''
    oauth = spotify_connect(app)
    payload = {'client_id': oauth.client_id, 
            'response_type': 'code', 'redirect_uri': oauth.redirect_uri,
            'scope': oauth.scope}
    r = requests.get(oauth.OAUTH_AUTHORIZE_URL, params=payload)
    return render_template('login.html', oauth=r.url)


@app.route('/home', methods=['POST', 'GET'])
def home():
    oauth = spotify_connect(app)
    response = oauth.get_access_token(request.args['code'])
    token = response['access_token']

    s = spotipy.Spotify(auth=token)
    offset = 0
    albums = s.current_user_saved_tracks(limit=50, offset=offset)
    return render_template('home.html', albums=albums['items'])
