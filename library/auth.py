from library import app
from library.app import create_app
from library.app import spotify_connect
from config import BaseConfig

from flask import render_template, request, redirect, url_for
from flask import session
import spotipy
import spotipy.util as util
import os
import base64
import requests


oauth = spotify_connect(app, scope=['user-library-read', 'playlist-read-collaborative',
                                'user-follow-read', 'playlist-modify-public'])


def refresh_token():
    ''' Manages exchange of refresh_token for a new access_token, helper function
    that's called in .login()
    '''
    if session['logged_in'] is True:
        if 'refresh' in session and 'token' in session:
            re_auth = base64.b64encode(oauth.client_id + ':' + oauth.client_secret)
            headers = {'Authorization': 'Basic {}'.format(str(re_auth))}
            payload = {'grant_type': 'refresh_token',
                       'refresh_token': session['refresh']}
            r = requests.post(oauth.OAUTH_TOKEN_URL, data=payload, headers=headers)
            if 'error' in  r.json():
                del session['token']
                del session['refresh']
                session['logged_in'] = False
                return redirect(url_for('login'))
            session['token'] = r.json()['access_token']
    else:
        print 'No session refresh.'
    return


@app.route('/login', methods=['POST', 'GET'])
@app.route('/', methods=['POST', 'GET'])
def login():
    '''prompts user to login via OAuth2 through Spotify
    this shows up in index.html

    if current_user.is_authenticated():
        return redirect(url_for('choose_parameters'))

    '''
    if 'logged_in' in session:
        if session['logged_in'] is True:
            return redirect(url_for('home'))
    payload = {'client_id': oauth.client_id,
        'response_type': 'code', 'redirect_uri': oauth.redirect_uri,
        'scope': oauth.scope}
    r = requests.get(oauth.OAUTH_AUTHORIZE_URL, params=payload)
    return render_template('login.html', oauth=r.url)


@app.route('/home', methods=['POST', 'GET'])
def home():
    if not 'token' in session:
        response = oauth.get_access_token(request.args['code'])
        session['token'] = response['access_token']
        session['refresh'] = response['refresh_token']
        session['logged_in'] = True
    else:
        refresh_token()
    s = spotipy.Spotify(auth=session['token'])
    offset = 0
    albums = s.current_user_saved_tracks(limit=50, offset=offset)
    return render_template('home.html', albums=albums['items'])
