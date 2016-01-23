
from library.app import create_app
from config import BaseConfig

from flask import render_template, request, redirect, url_for
import spotipy
import spotipy.util as util
import os
import requests

app = create_app()

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
    # utility of spotify.oauth2.SpotifyOauth
    # lets us store everythin in 1 container, as well as give us the auth URL
    oauth = spotipy.oauth.SpotifyOAuth(client_id=BaseConfig.CLIENT_ID,
                                        client_secret=BaseConfig.CLIENT_SECRET,
                                        redirect_uri=Baseconfig.REDIRECT_URI,
                                        scope='playlist-modify-public')

    # above doesn't build the actual URL, we do it via the requests library
    payload = {'client_id': oauth.client_id, 'client_secret': oauth.client_id,
                'response_type': 'code', 'redirect_uri': oauth.redirect_uri,
                'scope': oauth.scope}

    r = requests.get(oauth.OAUTH_AUTHORIZE_URL, params=payload)
    return r.url
    pass