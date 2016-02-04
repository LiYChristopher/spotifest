from library.app import app, login_manager
from library.app import app, celery, login_manager
from config import BaseConfig

from flask.ext.login import login_user, logout_user
from flask.ext.login import UserMixin
from flask import render_template, request, redirect, url_for
from flask import session
from wtforms import Form, StringField, validators
from wtforms.fields.html5 import DecimalRangeField

import redis
import spotipy
import spotipy.util as util
import base64
import requests
import helpers
import db


festival_id = None
did_user_sel_parameters = False


def oauth_prep(config=None, scope=['user-library-read']):
    ''' Connect to Spotify using spotipy & our app config credentials.
    'scope' should be a list. Multiple scopes will be processed below. '''

    scope = ' '.join(scope)
    oauth = spotipy.oauth2.SpotifyOAuth(client_id=config.CLIENT_ID,
                                client_secret=config.CLIENT_SECRET,
                                redirect_uri=config.REDIRECT_URI,
                                scope=scope)
    return oauth

scope = ['user-library-read', 'playlist-read-collaborative',
         'user-follow-read', 'playlist-modify-public']

oauth = oauth_prep(BaseConfig, scope)


class ParamsForm(Form):
    name = StringField('name',
                       [validators.DataRequired()],
                        default='Festify Test')
    danceability = DecimalRangeField('danceability',
                   [validators.NumberRange(min=0, max=1)],
                   default=0.5)
    hotttnesss = DecimalRangeField('hotttnesss',
                   [validators.NumberRange(min=0, max=1)],
                   default=0.5)
    energy = DecimalRangeField('energy',
                   [validators.NumberRange(min=0, max=1)],
                   default=0.5)    
    variety = DecimalRangeField('variety',
                   [validators.NumberRange(min=0, max=1)],
                   default=0.5)


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
    '''
    Manages exchange of refresh_token for a new access_token, if
    a user is logged in, allowing user to stay logged in for a long time.
    '''
    current_user = User.get(session.get('user_id'))
    if current_user:
        re_auth_in = BaseConfig.CLIENT_ID + ':' + BaseConfig.CLIENT_SECRET
        re_auth = base64.b64encode(re_auth_in)
        headers = {'Authorization': 'Basic {}'.format(str(re_auth))}
        payload = {'grant_type': 'refresh_token',
                   'refresh_token': current_user.refresh}
        r = requests.post(oauth.OAUTH_TOKEN_URL, data=payload, headers=headers)
        new_access = r.json()['access_token']
        current_user.access = new_access
    else:
        return redirect(url_for('home'))
    return


@app.before_request
def before_request():
    refresh()
    if session.get('user_id') and not User.users:
        logout_user()
    return


def login(config=BaseConfig, oauth=oauth):
    '''prompts user to login via OAuth2 through Spotify
    this shows up in index.html
    '''
    payload = {'client_id': oauth.client_id,
                'response_type': 'code',
                'redirect_uri': oauth.redirect_uri,
                'scope': oauth.scope}
    r = requests.get(oauth.OAUTH_AUTHORIZE_URL, params=payload)
    return r.url


@app.route('/', methods=['POST', 'GET'])
@app.route('/home', methods=['POST', 'GET'])
def home(config=BaseConfig, scope='user-library-read'):
    '''
    If no temporary code in request arguments, attempt to login user
    through Oauth.

    If there's a code (meaning successful sign-in to Spotify Oauth),
    and there is currently no users on the session cookie, go ahead and login
    the user to session.

    render home.html
    '''
    code = request.args.get('code')
    active_user = session.get('user_id')
    if request.method == 'GET':
        if not code and not active_user:
            auth_url = login()
            return render_template('home.html', login=False, oauth=auth_url)
        else:
            if code and not active_user:
                response = oauth.get_access_token(code)
                token = response['access_token']
                s = spotipy.Spotify(auth=token)
                user_id = s.me()['id']
                new_user = User(user_id, token, response['refresh_token'])
                login_user(new_user)
            # parameter form
            form = ParamsForm(csrf_enabled=False)
            active_user = session.get('user_id')
            current_user = User.users[active_user].access
            return render_template('home.html', form=form, login=True)

    if request.method == 'POST':
        # Did user click on join festival ?
        try:
            if request.form['festival_id']:
                print 'User selected join'
                auth_url = login()
                global festival_id
                festival_id = request.form['festival_id']
                return redirect(auth_url)
        except:
            if festival_id is None:
                print 'User did not click on join and selected parameter'
            else:
                print 'User selected parameters'

        # parameters
        name = request.form.get('name')
        h = request.form.get('hotttnesss')
        global did_user_sel_parameters
        did_user_sel_parameters = True
        d = request.form.get('danceability')
        e = request.form.get('energy')
        v = request.form.get('variety')
        current_user = User.users[active_user].access
        s = spotipy.Spotify(auth=current_user)
        user_id = s.me()['id']

        try:
            artists = helper.get_user_preferences(s)
            enough_data = True
        except:
            artists = helpers.suggested_artists
            enough_data = False

        processor = helpers.AsyncAdapter(app)
        artists = processor.get_user_preferences(s)
        catalog = helpers.random_catalog(artists)
        playlist = helpers.seed_playlist(catalog=catalog, hotttnesss=h,
                                         danceability=d, energy=e, variety=v)
        songs_id = processor.process_spotify_ids(50, 10, s, playlist)

        global festival_id
        if festival_id is not None and did_user_sel_parameters:
            '''
            This will need to be above and we will need
            to update the catalog instead of creating one
            or just add this playlist to existent playlist
            '''
            festival_information = db.get_info_from_database(festival_id)
            print 'festival id entered : ' + festival_id
            playlist_url = festival_information[3]
            id_playlist = festival_information[2]
            helpers.add_songs_to_playlist(s, user_id, id_playlist, songs_id)
            return render_template('results.html', playlist_url=playlist_url, enough_data=enough_data)
        else:
            helpers.create_playlist(s, user_id, name)
            id_playlist = helpers.get_id_from_playlist(s, user_id, name)
            helpers.add_songs_to_playlist(s, user_id, id_playlist, songs_id)
            playlist_url = 'https://embed.spotify.com/?uri=spotify:user:' + str(user_id) + ':playlist:' + str(id_playlist)
            if app.config['IS_ASYNC'] is True:
                db.save_to_database.apply_async(args=[name, user_id, id_playlist, playlist_url, catalog.id])
            else:
                db.save_to_database(name, user_id,id_playlist, playlist_url, catalog.id)
            return render_template('results.html', playlist_url=playlist_url,
                                    enough_data=enough_data)


@app.route('/festival/<url_slug>')
def festival(url_slug):
    return
