import random
import spotipy
import spotipy.util as util

from flask import Flask
from pyechonest import config
from pyechonest import playlist
from pyechonest import artist
from pyechonest.catalog import Catalog
from library.app import celery


config.ECHO_NEST_API_KEY = "SNRNTTK9UXTWYCMBH"

suggested_artists = set(['Radiohead', 'Nirvana', 'The Beatles', 'David Bowie',
                        'Aretha Franklin', 'Mogwai', 'Eels', 'Glass Animals',
                        'Grimes', 'Sungrazer', 'Queens of the Stone Age'])


class AsyncAdapter(object):
    '''
    an adapter class that encapsulates helper functions that have asynchronous
    options. The following helpers can be processed in via celery.
        - process_spotify_ids()
        - get_user_preferences()
    '''

    def __init__(self, app):
        if 'IS_ASYNC' not in app.config:
            raise KeyError("Please set config key 'IS_ASYNC' to True | False.")
        self.is_async = app.config['IS_ASYNC']

    def process_spotify_ids(self, total_items, chunk_size, spotipy, playlist):
        if not self.is_async:
            return self.non_async_process_spotify_ids(spotipy, playlist)
        else:
            if 'total_items' not in locals() or 'chunk_size' not in locals():
                raise ValueError("Missing arguments for async - 'total_items",
                                 "'chunk_size'")
            return self.async_process_spotify_ids(total_items, chunk_size,
                                             helper_args=[spotipy, playlist])

    def get_user_preferences(self, spotipy):
        if not self.is_async:
            return self.non_async_get_user_preferences(spotipy)
        else:
            return self.async_get_user_preferences(spotipy)

    def non_async_process_spotify_ids(self, spotipy, playlist):

        songs_id = get_songs_id(spotipy, playlist, None)
        return songs_id

    def async_process_spotify_ids(self, total_items, chunk_size, helper_args=[]):
        if not helper_args:
            return "stop"
        task_ids = []
        limit = total_items + chunk_size
        for chunk in xrange(0, limit, chunk_size):
            async_args = helper_args + [chunk]
            task = get_songs_id.apply_async(args=async_args)
            task_ids.append(task.task_id)
        songs_id = []
        while task_ids:
            for t in task_ids:
                cur_task = get_songs_id.AsyncResult(t)
                if cur_task.state == 'SUCCESS':
                    result = get_songs_id.AsyncResult(t).result
                    task_ids.remove(t)
                    songs_id += result
                else:
                    continue
        return songs_id

    def non_async_get_user_preferences(self, spotipy):
        # artists from saved tracks
        st = get_user_saved_tracks(spotipy)
        # artists form user playlists (public)
        up = get_user_playlists(spotipy)
        # artists from followed artists
        fa = get_user_followed(spotipy)
        return st | up | fa

    def async_get_user_preferences(self, spotipy):
        tasks = []
        preferences = set()
        # artists from saved tracks
        st = get_user_saved_tracks.apply_async(args=[spotipy])
        st_results = get_user_saved_tracks.AsyncResult(st.task_id)
        tasks.append(st_results)

        # artists form user playlists (public)
        up = get_user_playlists.apply_async(args=[spotipy])
        up_results = get_user_playlists.AsyncResult(up.task_id)
        tasks.append(up_results)

        # artists from followed artists
        fa = get_user_followed.apply_async(args=[spotipy])
        fa_results = get_user_followed.AsyncResult(fa.task_id)
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


@celery.task(name='saved_tracks')
def get_user_saved_tracks(spotipy):
    '''
    return a set with the saved tracks.
    for now it will return a set with only the artists
    '''
    offset = 0  # this set will be deleted if later we returns tracks instead of artists
    artists = {}
    while True:
        albums = spotipy.current_user_saved_tracks(limit=50, offset=offset)
        if not albums['items']:
            break
        batch = {item['track']['artists'][0]['name'] 
                    for item in albums['items']}
        artists.update(batch)
        offset += len(albums['items'])
    return artists


@celery.task(name='saved_playlists')
def get_user_playlists(spotipy):
    '''
    return a set with users tracks on playlist
    for now it will return a set with only the artists
    '''
    def show_tracks(results):
        '''
        helper function for get_user_playlists()
        '''
        for i, item in enumerate(tracks['items']):
            track = item['track']
            playlist_artists_list.append(track['artists'][0]['name'])

    playlist_artists_list = []
    offset = 0
    user_id = spotipy.current_user()['id']
    playlists = spotipy.user_playlists(user_id)

    for playlist in playlists['items']:
        owner = playlist['owner']['id']
        results = spotipy.user_playlist(owner, playlist['id'], fields="tracks,next")
        tracks = results['tracks']
        show_tracks(tracks)
        while tracks['next']:
            tracks = spotipy.next(tracks)
    return set(playlist_artists_list)


@celery.task(name='followed_users')
def get_user_followed(spotipy):
    '''
    return a set with artists followed by artist.
    '''
    followed = spotipy.current_user_followed_artists()
    artists = {artist['name'] for artist in followed['artists']['items']}
    return artists


def search_artist_echonest(name):

    # add validation via echonest here
    results = artist.search(name=name)
    if results is False:
        return results
    else:
        sorted_results = sorted([art.name for art in results])
        int_results = [(x, sorted_results[x]) for x in xrange(1, len(sorted_results))]
    return int_results


def create_playlist(spotipy, user_id, name_playlist):
    '''
    Function that will create a playlist por a user
    with name provided
    user_id = current_user['id']
    '''
    spotipy.user_playlist_create(user_id, name_playlist, public=True)
    print 'playlist created'


def add_songs_to_playlist(spotipy, user_id, playlist_id, id_songs):
    '''
    add songs to a playlist providing user, id playlist
    and a list of songs
    '''
    spotipy.user_playlist_add_tracks(user_id, playlist_id, id_songs)
    print 'track added to playlist'


def get_id_from_playlist(spotipy, user_id, name_playlist):
    '''
    function that return the id of a playlist
    providing the id
    '''
    offset = 0
    playlists = spotipy.user_playlists(user_id)
    user_playlists = {}  # This will stored the users playlists
    for playlist in playlists['items']:
        if playlist['name'] == name_playlist:
            return playlist['id']
    return 'Could not find id of new playlist'


def insert_to_catalog(catalog, item):
    ready = process_to_item(item)
    ticket = catalog.update(ready)
    return ticket


def process_to_item(artist):
    ''' Converts artist or song object into a formatted
    item to be inserted into a Catalog object.'''
    item = [{}]
    item[0]['action'] = 'update'
    item[0]['item'] = {}
    item[0]['item']['artist_name'] = artist
    return item


def random_catalog(artists, limit=15, catalog_id=None):
    if catalog_id:
        catalog = Catalog(catalog_id)
    else:
        catalog = Catalog('your_catalog', 'general')
    artists = list(artists)
    for _ in xrange(limit):
        choice = random.choice(artists)
        insert_to_catalog(catalog, choice)
    return catalog


def seed_playlist(catalog, danceability=0.5, hotttnesss=0.5,
                  energy=0.5, variety=0.5, adventurousness=0.5,
                  results=50):
        ''' Allow user to adjust:
        - style
    '''
    # write a wrapper around playlist.static() spotify obj, so extra params
    # can be set before instantiating the playlist.

        pl = playlist.static(type='catalog-radio', seed_catalog=catalog,
                             min_danceability=danceability, artist_min_hotttnesss=hotttnesss,
                             min_energy=energy, variety=variety, adventurousness=adventurousness,
                             distribution='focused',
                             results=results)
        print 'songs in playslist', len(pl)
        #catalog.delete()
        return pl


@celery.task(name='song_ids')
def get_songs_id(spotipy, playlist, offset):
    '''
    get a list of sgons names and return list of songs ids
    '''
    songs_id = []
    # full playlist
    if offset is None:
        playlist = playlist
    # playlist chunk
    elif isinstance(offset, int):
        playlist = playlist[offset:offset + 10]
    for item in playlist:
        q = "track:{} artist:{}".format(item.title.encode('utf-8'),
                                        item.artist_name.encode('utf-8'))

        result = spotipy.search(q, type='track', limit=1)
        if not result['tracks'].get('items'):
            continue
        spotify_id = spotipy.search(q, type='track', limit=1)['tracks']['items'][0]['id']
        songs_id.append(spotify_id)
    return songs_id
