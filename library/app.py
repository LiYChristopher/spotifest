#creates the app and can include a config.py
from flask import Flask
from config import BaseConfig
import spotipy
import spotipy.util as util
import os
import requests
import json


# from library import auth_check


def create_app(config=None, app_name=None, blueprints=None):
    app = Flask(__name__)
    return app


def spotify_connect(app, config=None, scope=['user-library-read']):
    ''' Connect to Spotify using spotipy & our app config credentials.
    'scope' should be a list. Multiple scopes will be processed below. '''

    scope = ' '.join(scope)
    oauth = spotipy.oauth2.SpotifyOAuth(client_id=BaseConfig.CLIENT_ID,
                                client_secret=BaseConfig.CLIENT_SECRET,
                                redirect_uri=BaseConfig.REDIRECT_URI,
                                scope=scope)

    return oauth

