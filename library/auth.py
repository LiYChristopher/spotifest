from library import app, login_manager
from library.app import create_app, spotify_connect
from config import BaseConfig

from flask.ext.login import LoginManager, login_user
from flask.ext.login import UserMixin
from flask import render_template, request, redirect, url_for
from flask import session
import spotipy
import spotipy.util as util
import base64
import requests


oauth = spotify_connect(app, scope=['user-library-read', 'playlist-read-collaborative',
                                'user-follow-read', 'playlist-modify-public'])

class User(UserMixin):

    users = {}

    def __init__(self, spotify_id, access_token, refresh_token):
        self.id = unicode(spotify_id)
        self.access = access_token 
        self.refresh = refresh_token
        self.users[self.id] = self

    @classmethod
    def get(cls, user_id):
        if cls.users:
            if user_id in cls.users:
                return cls.users[user_id]
        else:
            return None


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@login_manager.needs_refresh_handler
def refresh():
    ''' Manages exchange of refresh_token for a new access_token, helper function
    thats called in .login()
    '''
    current_user = User.get(session.get('user_id'))
    if current_user:
        re_auth = base64.b64encode(oauth.client_id + ':' + oauth.client_secret)
        headers = {'Authorization': 'Basic {}'.format(str(re_auth))}
        payload = {'grant_type': 'refresh_token',
                   'refresh_token': current_user.refresh}
        r = requests.post(oauth.OAUTH_TOKEN_URL, data=payload, headers=headers)
        new_access = r.json()['access_token']
        current_user.access = new_access
    else:
        return redirect(url_for('login'))
    return


@app.before_request
def before_request():
    refresh()
    return


@app.route('/login', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
def login():
    '''prompts user to login via OAuth2 through Spotify
    this shows up in index.html

    if current_user.is_authenticated():
        return redirect(url_for('choose_parameters'))
    '''
    if session.get('user_id'):
        return redirect(url_for('home'))
    payload = {'client_id': oauth.client_id,
        'response_type': 'code', 'redirect_uri': oauth.redirect_uri,
        'scope': oauth.scope}
    r = requests.get(oauth.OAUTH_AUTHORIZE_URL, params=payload)
    return render_template('login.html', oauth=r.url)


@app.route('/home', methods=['POST', 'GET'])
def home():
    if not session.get('user_id'):
        response = oauth.get_access_token(request.args['code'])
        s = spotipy.Spotify(auth=response['access_token'])
        user = User(s.me()['id'], response['access_token'], response['refresh_token'])
        login_user(user)
    access_token = User.get(session.get('user_id')).access
    s = spotipy.Spotify(auth=access_token)
    offset = 0
    albums = s.current_user_saved_tracks(limit=50, offset=offset)
    return render_template('home.html', albums=albums['items'])
