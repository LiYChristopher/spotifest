from library.app import app, celery, login_manager
from config import BaseConfig

from flask.ext.login import login_user
from flask.ext.login import UserMixin
from flask import render_template, request, redirect, url_for
from flask import session
import redis
import spotipy
import spotipy.util as util
import base64
import requests
import helpers


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


def process_spotify_ids(total_items, chunk_size, helper_args=[]):
    '''
    Wrapper function that will start/run concurrent conversions of
    artist/song names to spotify IDs via celery. Returns list of
    all song_ids
    '''
    if not helper_args:
        return "stop"
    task_ids = []
    limit = total_items + chunk_size
    for chunk in xrange(0, limit, chunk_size):
        async_args = helper_args + [chunk]
        task = helpers.get_songs_id.apply_async(args=async_args)
        #print "adding {} to queue.".format(task.task_id)
        task_ids.append(task.task_id)
    songs_id = []
    while task_ids:
        for t in task_ids:
            cur_task = helpers.get_songs_id.AsyncResult(t)
            if cur_task.state == 'SUCCESS':
                result = helpers.get_songs_id.AsyncResult(t).result
                task_ids.remove(t)
                songs_id += result
            else:
                continue
    return songs_id

def get_user_preferences(spotipy):
    '''
    wrapper for all the user preference helper functions,
    returning a single set with all artists listened to from a user.
    '''
    tasks = []
    preferences = set()
    # artists from saved tracks
    st = helpers.get_user_saved_tracks.apply_async(args=[spotipy])
    st_results = helpers.get_user_saved_tracks.AsyncResult(st.task_id)
    tasks.append(st_results)
    # artists form user playlists (public)
    up = helpers.get_user_playlists.apply_async(args=[spotipy])
    up_results = helpers.get_user_playlists.AsyncResult(up.task_id)
    tasks.append(up_results)
    # artists from followed artists
    fa = helpers.get_user_followed.apply_async(args=[spotipy])
    fa_results = helpers.get_user_followed.AsyncResult(fa.task_id)
    tasks.append(fa_results)
    while tasks:
        for t in tasks:
            if t.state == 'SUCCESS':
                result = t.result
                tasks.remove(t)
                preferences = preferences | set(result)
            else:
                continue
    return preferences


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

    if request.method == 'GET':
        if not 'code' in request.args:
            auth_url = login()
            return render_template('home.html', login=False, oauth=auth_url)
        else:
            if not User.users or not session.get('user_id'):
                 # log user to session (Flask-Login)
                response = oauth.get_access_token(request.args['code'])
                token = response['access_token']
                s = spotipy.Spotify(auth=token)
                user_id = s.me()['id']
                new_user = User(user_id, token, response['refresh_token'])
                login_user(new_user)
            current_user = User.users[session.get('user_id')].access

            s = spotipy.Spotify(auth=current_user)
            offset = 0
            albums = s.current_user_saved_tracks(limit=50, offset=offset)
            return render_template('home.html', albums=albums['items'],
                                    login=True)
    if request.method == 'POST':
        current_user = User.users[session.get('user_id')].access
        s = spotipy.Spotify(auth=current_user)
        user_id = s.me()['id']

        artists = get_user_preferences(s)
        catalog = helpers.random_catalog(artists)
        playlist = helpers.seed_playlist(catalog)
        songs_id = process_spotify_ids(50, 10, helper_args=[s, playlist])

        helpers.create_playlist(s, user_id, 'Festify Test')
        id_playlist = helpers.get_id_from_playlist(s, user_id, 'Festify Test')
        helpers.add_songs_to_playlist(s, user_id, id_playlist, songs_id)
        playlist_url = 'https://embed.spotify.com/?uri=spotify:user:' + str(user_id) + ':playlist:' + str(id_playlist)
        return render_template('results.html', playlist_url=playlist_url)
