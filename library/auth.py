from library.app import app, login_manager
from library.helpers import get_user_preferences, suggested_artists
from library.helpers import random_catalog, seed_playlist
from library import frontend_helpers
from config import BaseConfig

from flask.ext.login import login_user
from flask.ext.login import UserMixin
from flask.ext.wtf import Form
from flask import render_template, request, redirect, url_for, session

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


class User(UserMixin):

    users = {}

    def __init__(self, spotify_id, access_token, refresh_token, artists=set(),
                search_results=None):
        self.id = unicode(spotify_id)
        self.access = access_token
        self.refresh = refresh_token
        self.users[self.id] = self
        self.artists = artists
        self.search_results = search_results

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
def home(config=BaseConfig):
    '''
    If no temporary code in request arguments, attempt to login user
    through Oauth.

    If there's a code (meaning successful sign-in to Spotify Oauth),
    and there is currently no users on the session cookie, go ahead and login
    the user to session.

    render home.html
    '''

    new = None
    new_artist = None
    searchform = frontend_helpers.SearchForm()
    suggested_pl_butt = frontend_helpers.SuggestedPlaylistButton()
    art_select = frontend_helpers.ArtistSelect(request.form)

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
            try:
                get_user_preferences(s)
                print (get_user_preferences(s))
                User.artists = get_user_preferences(s)
            except:
                User.artists = set()
            artists = User.artists

    else:
        if searchform.validate_on_submit():
            new_artist = searchform.artist_search.data
            User.search_results = helpers.search_artist_echonest(new_artist)
            art_select.artist_display.choices = User.search_results
            if not User.search_results:
                new = -1

        if art_select.artist_display.data:
            if art_select.is_submitted():
                option_n = int(art_select.artist_display.data) + 1
                chosen_art = User.search_results[option_n][1]
                if chosen_art not in User.artists:
                    User.artists.update([chosen_art])
                    new_artist = chosen_art
                    new = 1
                else:
                    new = 0


        elif suggested_pl_butt.validate_on_submit():
            if request.form.get("add_button"):
                new_artist = ', '.join(suggested_artists)
                User.artists.update(suggested_artists)
                artists = User.artists
                new = True

    return render_template('home.html', login=True, searchform=searchform,
                            art_select=art_select,
                            suggested_pl_butt=suggested_pl_butt,
                            artists=User.artists,
                            new=new, new_artist=new_artist)




@app.route('/setlist_prep', methods=['POST', 'GET'])
def set_prep():
    pass



@app.route('/results', methods=['POST', 'GET'])
def results():
    if request.method == 'POST':
        current_user = User.users[session.get('user_id')].access
        s = spotipy.Spotify(auth=current_user)
        user_id = s.me()['id']
        try:
            get_user_preferences(s)
            print (get_user_preferences(s))
            User.artists = get_user_preferences(s)
            enough_data = True
        except:
            User.artists = suggested_artists
            enough_data = False
        catalog = random_catalog(User.artists)
        playlist = seed_playlist(catalog)
        songs_id = helpers.get_songs_id(s, playlist)
        helpers.create_playlist(s, user_id, 'Festify Test')
        id_playlist = helpers.get_id_from_playlist(s, user_id, 'Festify Test')
        helpers.add_songs_to_playlist(s, user_id, id_playlist, songs_id)
        uid = str(user_id)
        plid = str(playlist_id)
        playlist_url = 'https://embed.spotify.com/?uri=spotify:user:{}:playlist:{}'.format(uid, plid)
        return render_template('results.html', playlist_url=playlist_url,
                                enough_data=enough_data)
