#creates the app and can include a config.py


from flask import Flask
from config import BaseConfig
import spotipy
import spotipy.util as util
import os
import requests


# from library import auth_check

def create_app(config=None, app_name=None, blueprints=None):
    app = Flask(__name__)
    return app


def spotify_connect(app, config=None, scope='playlist-modify-public'):
    """ Connect to Spotify using spotipy & our app config credentials"""
    # all creds in 1 container EXCEPT scope (to be added later)
    oauth = spotipy.oauth2.SpotifyOAuth(client_id=config.CLIENT_ID,
                                client_secret=config.CLIENT_SECRET,
                                redirect_uri=config.REDIRECT_URI,
                                scope=scope)

    # make dictionary for URL through requests library
    payload = {'client_id': oauth.client_id, 'client_secret': oauth.client_id,
                'response_type': 'code', 'redirect_uri': oauth.redirect_uri,
                'scope': oauth.scope}

    r = requests.get(oauth.OAUTH_AUTHORIZE_URL, params=payload)
    return r.url