from library import app, celery, login_manager
from library.helpers import (suggested_artists, random_catalog, seed_playlist)
from library import frontend_helpers
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
import base64
import requests
import helpers
import db


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
                 search_results=list(), festival_name=None):
        self.artists = {}
        self.hotness = hotness
        self.danceability = danceability
        self.energy = energy
        self.variety = variety
        self.adventurousness = adventurousness
        self.organizer = organizer
        self.search_results = search_results
        self.festival_name = festival_name
        self.user_id = None
        self.user_festivals = None
        self.did_user_sel_parameters = False
        self.festival_id = None

    def save_preferences(self, artists, urlSlug):
        if not isinstance(artists, set):
            raise TypeError('Artist data not a set object.')
        _current_user = str(session.get('user_id'))
        if not self.artists.get(_current_user):
            self.artists[_current_user] = {}
        self.artists[_current_user][urlSlug] = artists
        return

    def retrieve_preferences(self, urlSlug):
        _current_user = str(session.get('user_id'))
        if not self.artists.get(_current_user):
            return None
        elif not self.artists[_current_user].get(urlSlug):
            return None
        else:
            return self.artists[_current_user][urlSlug]

    def update_preferences(self, artists, urlSlug):
        _current_user = str(session.get('user_id'))
        if not isinstance(artists, set):
            raise TypeError('Artist data not a set object.')
        cur_preferences = self.artists[_current_user][urlSlug]
        print "length before...", len(cur_preferences)
        print "{} about to be added to cur_preferences".format(artists)
        self.artists[_current_user][urlSlug] = cur_preferences | artists
        print "length after...", len(self.artists[_current_user][urlSlug])
        return

    def delete_preferences(self):
        _current_user = str(session.get('user_id'))
        del self.artists[_current_user]
        return


def festify_logout():
    if load_user(session.get('user_id')):
        user_cache.delete_preferences()
    logout_user()
    return

user_cache = UserCache()


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
    if session.get('user_id') and not load_user(session.get('user_id')):
        festify_logout()
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

    user_cache.user_festivals = db.get_user_festivals(user_cache.user_id)

    if request.method == 'POST':
        url_slug = request.form['festival_id']
        print ("FESTIVAL ID OR URL SLUGGY IS {}".format(url_slug))
        return redirect(url_for('join', url_slug=url_slug))
    return render_template('home.html', login=True,
                            user_festivals=user_cache.user_festivals,
                            user_id=user_cache.user_id)


@app.route('/festival/join/<url_slug>', methods=['GET'])
@login_required
def join(url_slug):
    print ("URLSLUG HERE IS {}".format(url_slug))
    current_festival = db.get_info_from_database(url_slug)
    if not current_festival:
        flash(("Festival '{}' does not exist! Please check"
               " the code and try again.").format(url_slug))
        return redirect(url_for('home'))
    organizer = current_festival[2]
    _user = session.get('user_id')
    if organizer != _user:
        try:
            db.save_contributor(current_festival[0], _user)
        except:
            print ("Contributor {} is already in the database.".format(_user))
    else:
        flash("Welcome back to your own festival!")
    return redirect(url_for('festival', url_slug=url_slug))


@app.route('/festival/create_new', methods=['GET'])
@login_required
def new():
    current_user = load_user(session.get('user_id'))
    new_url_slug = helpers.generate_urlslug(current_user.id)
    new_catalog = helpers.Catalog(new_url_slug, 'general')
    s = spotipy.Spotify(auth=current_user.access)

    processor = helpers.AsyncAdapter(app)
    user_cache.save_preferences(processor.get_user_preferences(s), new_url_slug)
    artists = user_cache.retrieve_preferences(new_url_slug)

    if user_cache.retrieve_preferences(new_url_slug):
        processor.populate_catalog(artists, 3, catalog=new_catalog)
    if app.config['IS_ASYNC'] is True:
        save_task = db.save_to_database.apply_async(args=[None, current_user.id,
                                                    None, None, new_catalog.id,
                                                    new_url_slug])
        while True:
            if save_task.state == 'SUCCESS':
                print 'just saved DB'
                break
    else:
        db.save_to_database(None, current_user.id, None, None,
                            new_catalog.id, new_url_slug)

    current_festival = db.get_info_from_database(new_url_slug)
    festivalId = current_festival[0]
    userId = current_festival[2]
    try:
        db.save_contributor(festivalId, userId, organizer=1, ready=1)
    except:
        print ("SAVING CONTRIBUTOR FAILED!")
    return redirect(url_for('festival', url_slug=new_url_slug))


@app.route('/festival/<url_slug>', methods=['GET', 'POST'])
@login_required
def festival(url_slug):
    current_festival = db.get_info_from_database(url_slug)
    user_cache.cur_festival_id = current_festival[0]
    if user_cache.artists:
        for person in user_cache.artists.keys():
            print "Person: ", person
            if user_cache.artists[person].keys():
                print "Festivals Active in: ", user_cache.artists[person].keys()

    if not current_festival:
        flash(("Festival '{}' does not exist! Please check"
               "the code and try again.").format(url_slug))
        return redirect(url_for('home'))

    organizer = current_festival[2]
    _user = session.get('user_id')
    is_org = True
    # check if organizer & if so, find name
    if organizer != _user:
        is_org = False
        festival_name = current_festival[1]
    elif organizer == _user:
        is_org = True
        festival_name = None
    # fetch contributors: the 0th term = the main organizer!
    try:
        all_users = db.get_contributors(current_festival[0])
        if all_users is None:
            flash(("Festival '{}' is having problems. Please check with the "
                "organizer. Try again later.").format(url_slug))
            return redirect(url_for('home'))
    except:
        flash(("Festival '{}' is having problems. Please check with the "
                "organizer. Try again later.").format(url_slug))
        return redirect(url_for('home'))

    new = None
    new_artist = None

    current_user = load_user(session.get('user_id')).access
    s = spotipy.Spotify(auth=current_user)
    try:
        if not user_cache.retrieve_preferences(url_slug):
            processor = helpers.AsyncAdapter(app)
            artists = processor.get_user_preferences(s)
            user_cache.save_preferences(artists, url_slug)
        else:
            print "CURRENT NUM of ARTISTS", len(user_cache.retrieve_preferences(url_slug))
    except:
        print ("No artists followed found in the user's Spotify account.")

    # prep forms
    searchform = frontend_helpers.SearchForm()
    suggested_pl_butt = frontend_helpers.SuggestedPlaylistButton()
    art_select = frontend_helpers.ArtistSelect(request.form)
    params_form = frontend_helpers.ParamsForm()

    if searchform.validate_on_submit():
        s_artist = searchform.artist_search.data
        user_cache.search_results = helpers.search_artist_echonest(s_artist)
        art_select.artist_display.choices = user_cache.search_results

    if art_select.artist_display.data:
        if art_select.is_submitted():
            option_n = int(art_select.artist_display.data) - 1
            chosen_art = user_cache.search_results[option_n][1]
            cur_user_preferences = user_cache.retrieve_preferences(url_slug)
            if chosen_art not in cur_user_preferences:
                print "ADDING CHOSEN ART", chosen_art
                user_cache.update_preferences(set([chosen_art]), url_slug)
                new_artist = chosen_art
                new = 1
            else:
                new = 0
            # user_cache.search_results = list()

    elif suggested_pl_butt.validate_on_submit():
        if request.form.get("add_button"):
            new_artist = ', '.join(suggested_artists)
            user_cache.update_preferences(set([chosen_art]), url_slug)
            new = True

    return render_template('festival.html', url_slug=url_slug,
                           s_results=user_cache.search_results,
                           art_select=art_select, searchform=searchform,
                           suggested_pl_butt=suggested_pl_butt,
                           artists=user_cache.artists,
                           params_form=params_form,
                           all_users=all_users,
                           festival_name=festival_name,
                           user=_user,
                           new=new, new_artist=new_artist, is_org=is_org)


@app.route('/festival/<url_slug>/update_parameters', methods=['POST'])
def update_parameters(url_slug):
    '''
    If not the owner, update contributor's parameters on database.
    '''
    _user = session.get('user_id')
    current_festival = db.get_info_from_database(url_slug)
    festivalId = current_festival[0]
    catalog_id = current_festival[5]
    catalog = helpers.Catalog(catalog_id)
    artists = user_cache.retrieve_preferences(url_slug)
    processor = helpers.AsyncAdapter(app)
    processor.populate_catalog(artists, 3, catalog=catalog)

    festivalId = db.get_info_from_database(url_slug)[0]
    h = request.form.get('hotttnesss')
    d = request.form.get('danceability')
    e = request.form.get('energy')
    v = request.form.get('variety')
    a = request.form.get('adventurousness')
    db.update_parameters(festivalId, _user, h, d, e, v, a)
    flash("You've pitched the perfect festival to the organizer." +
          " Now we wait.")
    return redirect(url_for('festival', url_slug=url_slug))


@app.route('/festival/<url_slug>/results', methods=['POST', 'GET'])
def results(url_slug):
    current_festival = db.get_info_from_database(url_slug)
    festival_catalog = current_festival[5]

    if request.method == 'POST':
        # Did user click on join festival ?
        try:
            if request.form['festival_id']:
                print 'User selected join'
                auth_url = login()
                user_cache.festival_id = request.form['festival_id']
                return redirect(auth_url)
        except:
            if user_cache.festival_id is None:
                print 'User did not click on join and selected parameter'
            else:
                print 'User selected parameters'

        if not user_cache.artists:
            flash("You really should add some artists!"
                  " Maybe you can use our suggestions..")
            return redirect(url_for('home'))

        # parameters
        enough_data = True
        name = request.form.get('name')
        h = request.form.get('hotttnesss')
        d = request.form.get('danceability')
        e = request.form.get('energy')
        v = request.form.get('variety')
        a = request.form.get('adventurousness')
        user_cache.did_user_sel_parameters = True
        current_user = load_user(session.get('user_id')).access
        # db.update_parameters(festivalId, _user, h, d, e, v, a)
        s = spotipy.Spotify(auth=current_user)
        user_id = s.me()['id']

        # db.get_average_parameters(user_cache.current_festival)
        processor = helpers.AsyncAdapter(app)
        playlist = helpers.seed_playlist(catalog=festival_catalog, hotttnesss=h,
                                         danceability=d, energy=e, variety=v,
                                         adventurousness=a)
        songs_id = processor.process_spotify_ids(50, 10, s, playlist)

        if user_cache.festival_id is not None and user_cache.did_user_sel_parameters:
            '''
            This will need to be above and we will need
            to update the catalog instead of creating one
            or just add this playlist to existent playlist
            '''
            festival_information = db.get_info_from_database(festival_id)
            playlist_url = festival_information[4]
            id_playlist = festival_information[3]
            helpers.add_songs_to_playlist(s, user_id, id_playlist, songs_id)
            return render_template('results.html', playlist_url=playlist_url,
                                   enough_data=enough_data)
        else:
            helpers.create_playlist(s, user_id, name)
            id_playlist = helpers.get_id_from_playlist(s, user_id, name)
            helpers.add_songs_to_playlist(s, user_id, id_playlist, songs_id)
            u_id = str(user_id)
            id_pl = str(id_playlist)
            playlist_url = ('https://embed.spotify.com/?uri=spotify:user:'
                            '{}:playlist:{}'.format(u_id, id_pl))
            if app.config['IS_ASYNC'] is True:
                db.update_festival.apply_async(args=[name, id_playlist,
                                               playlist_url, url_slug])
            else:
                db.update_festival(name, id_playlist, playlist_url, url_slug)
            return render_template('results.html', playlist_url=playlist_url,
                                   enough_data=enough_data)


@app.errorhandler(401)
def access_blocked(error):
    auth_url = login()
    flash('Please login with your Spotify account before continuing!')
    return render_template('home.html', login=False, oauth=auth_url)
