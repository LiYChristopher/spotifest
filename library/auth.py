from library.app import app, login_manager
from library.helpers import (suggested_artists, random_catalog, seed_playlist)
from library import frontend_helpers
from library.app import app, celery, login_manager
from config import BaseConfig

from flask.ext.login import login_user, logout_user
from flask.ext.login import UserMixin
from flask import render_template, request, redirect, url_for
from flask import session, flash

from flask.ext.login import login_user, logout_user, login_required, UserMixin
from flask.ext.wtf import Form
from flask import render_template, request, redirect, url_for, session, flash

import redis
import spotipy
import spotipy.util as util
import os
import base64
import hashlib
import datetime
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


class User(UserMixin):

    users = {}

    def __init__(self, spotify_id, access_token, refresh_token, artists=set(),
                search_results=None):
        self.id = unicode(spotify_id)
        self.access = access_token
        self.refresh = refresh_token
        self.artists = artists
        self.search_results = search_results
        self.users[self.id] = self

    @classmethod
    def get(cls, user_id):
        if cls.users:
            if user_id in cls.users:
                return cls.users[user_id]
        else:
            return None

class UserCache():
    def __init__(self, artists=set(), hotness=None, danceability=None, enery=None,
                energy=None, variety=None, adventurousness=None, organizer=0,
                search_results=list()):
        self.artists = artists
        self.hotness = hotness
        self.danceability = danceability
        self.energy = energy
        self.variety = variety
        self.adventurousness = adventurousness
        self.organizer = organizer
        self.search_results = search_results

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
def home(config=BaseConfig):
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

            if not User.users or not session.get('user_id'):

                # log user to session (Flask-Login)
                response = oauth.get_access_token(request.args['code'])
                token = response['access_token']
                s = spotipy.Spotify(auth=token)
                user_id = s.me()['id']
                new_user = User(user_id, token, response['refresh_token'])
                login_user(new_user)
            # at this point, user is logged in, so if you click "Create"

            current_user = load_user(session.get('user_id')).access
            s = spotipy.Spotify(auth=current_user)

    if request.method == 'POST':
        url_slug = request.form['festival_id']
        return redirect(url_for('festival', url_slug=url_slug))
    return render_template('home.html', login=True)


@app.route('/festival/create_new', methods=['GET'])
@login_required
def new():
    current_user = load_user(session.get('user_id'))
    unique = base64.b64encode(os.urandom(3))
    slug_hash = hashlib.md5(current_user.id + str(datetime.datetime.now()) + unique)
    new_url_slug = slug_hash.hexdigest()[:7]
    new_catalog = helpers.Catalog(new_url_slug, 'general')
    s = spotipy.Spotify(auth=current_user.access)
    if app.config['IS_ASYNC'] is True:
        processor = helpers.AsyncAdapter(app)
        artists = processor.get_user_preferences(s)
        helpers.random_catalog(artists, catalog_id=new_catalog.id)
        save_task = db.save_to_database.apply_async(args=[None, current_user.id, 
                                    None, None, new_catalog.id, new_url_slug])
        while True:
            if save_task.state == 'SUCCESS':
                break
    else:
        db.save_to_database(None, current_user.id, None, None, 
                            new_catalog.id, new_url_slug)

    current_festival = db.get_info_from_database(urlSlug=new_url_slug)
    festivalId = current_festival[0]
    userId = current_festival[2]
    try:
        db.save_contributor(festivalId, userId, organizer=1)
    except:
        print ("SAVING CONTRIBUTOR FAILED!")
    return redirect(url_for('festival', url_slug=new_url_slug))


@app.route('/festival/<url_slug>', methods=['GET', 'POST'])
@login_required
def festival(url_slug):

    current_festival = db.get_info_from_database(url_slug)
    if not current_festival:
        flash(("Festival '{}' does not exist! Please check"
                "the code and try again.").format(url_slug))
        return redirect(url_for('home'))
    owner = current_festival[2]
    _user = session.get('user_id')
    is_owner = True
    user_cache = UserCache()

    # save contributor if new
    if owner != _user:
        is_owner = False
        festival_name = current_festival[1]
        try:
            db.save_contributor(current_festival[0], _user)
        except:
            print ("Contributor {} is already in the database.".format(_user))
    elif owner == _user:
        is_owner = True
        festival_name = None

    #fetch contributors: the 0th term = the main organizer!
    try:
        contributors = db.get_contributors(current_festival[0])
        organizer = contributors.pop(0)
    except:
        flash(("Festival '{}' is having problems.. please check with the organizer."
                "Try the code and try again.").format(url_slug))
        return redirect(url_for('home'))


    new = None
    new_artist = None
    searchform = frontend_helpers.SearchForm()
    suggested_pl_butt = frontend_helpers.SuggestedPlaylistButton()
    art_select = frontend_helpers.ArtistSelect(request.form)
    params_form = frontend_helpers.ParamsForm()


    current_user = load_user(session.get('user_id')).access
    s = spotipy.Spotify(auth=current_user)
    try:
        processor = helpers.AsyncAdapter(app)
        artists = processor.get_user_preferences(s)
        print (artists)
        user_cache.artists = artists
    except:
        print ("No artists followed found in the user's Spotify account.")

    if searchform.validate_on_submit():
        s_artist = searchform.artist_search.data
        user_cache.search_results = helpers.search_artist_echonest(s_artist)
        art_select.artist_display.choices = user_cache.search_results


    if art_select.artist_display.data:
        if art_select.is_submitted():
            option_n = int(art_select.artist_display.data) - 1
            chosen_art = user_cache.search_results[option_n][1]
            if chosen_art not in user_cache.artists:
                user_cache.artists.update(set(chosen_art))
                new_artist = chosen_art
                new = 1
            else:
                new = 0

    elif suggested_pl_butt.validate_on_submit():
        if request.form.get("add_button"):
            new_artist = ', '.join(suggested_artists)
            user_cache.artists.update(set(suggested_artists))
            new = True    

    return render_template('festival.html', url_slug=url_slug, 
                            s_results=user_cache.search_results,
                            art_select=art_select, searchform=searchform, 
                            suggested_pl_butt=suggested_pl_butt,
                            artists=user_cache.artists,
                            params_form=params_form,
                            organizer=organizer,
                            contributors=contributors,
                            festival_name=festival_name,
                            new=new, new_artist=new_artist, is_owner=is_owner)


@app.route('/festival/<url_slug>/results', methods=['POST', 'GET'])
def results(url_slug):
    current_festival = db.get_info_from_database(url_slug)
    festival_catalog = current_festival[4]

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

        if not user_cache.artists:
            flash('You really should add some artists! Maybe you can use our suggestions..')
            return redirect(url_for('home'))

        # parameters
        enough_data = True
        name = request.form.get('name')
        h = request.form.get('hotttnesss')
        global did_user_sel_parameters
        did_user_sel_parameters = True
        d = request.form.get('danceability')
        e = request.form.get('energy')
        v = request.form.get('variety')
        a = request.form.get('adventurousness')
        current_user = load_user(session.get('user_id')).access
        s = spotipy.Spotify(auth=current_user)
        user_id = s.me()['id']

        processor = helpers.AsyncAdapter(app)
        playlist = helpers.seed_playlist(catalog=festival_catalog, hotttnesss=h,
                                         danceability=d, energy=e, variety=v,
                                         adventurousness=a)
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
                db.update_festival.apply_async(args=[name, id_playlist, playlist_url, url_slug])
            else:
                db.update_festival(name, id_playlist, playlist_url, url_slug)
            return render_template('results.html', playlist_url=playlist_url,
                                    enough_data=enough_data)


@app.errorhandler(401)
def access_blocked(error):
    auth_url = login()
    flash('Please login with your Spotify account before continuing!')
    return render_template('home.html', login=False, oauth=auth_url)



