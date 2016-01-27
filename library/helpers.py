import spotipy
import spotipy.util as util

from pyechonest import config
from pyechonest import playlist
from pyechonest.catalog import Catalog

import random

config.ECHO_NEST_API_KEY = "SNRNTTK9UXTWYCMBH"

def get_user_preferences(spotipy):
    """
    wrapper for all the user preference helper functions,
    returning a single set with all artists listened to from a user.
    """
    # artists from saved tracks
    from_saved_tracks = get_user_saved_tracks(spotipy)
    # artists form user playlists (public)
    from_user_playlists = get_user_playlists(spotipy)
    # artists from followed artists
    from_followed_artists = get_user_followed(spotipy)
    return from_saved_tracks | from_user_playlists | from_followed_artists


def get_user_saved_tracks(spotipy):
    """
    return a set with the saved tracks.
    for now it will return a set with only the artists
    """
    offset = 0
    artists = set()  # this set will be deleted if later we returns tracks instead of artists
    while True:
        albums = spotipy.current_user_saved_tracks(limit=50, offset=offset)
        if not albums['items']:
            break
        for item in albums['items']:
            track = item['track']
            artists.add(track['artists'][0]['name'])
        offset += len(albums['items'])
    return artists


def get_user_playlists(spotipy):
    """
    return a set with users tracks on playlist
    for now it will return a set with only the artists
    """
    def show_tracks(results):
        """
        helper function for get_user_playlists()
        """
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

def get_user_followed(spotipy):
    """
    return a set with artists followed by artist.
    """
    artists = set()
    followed = spotipy.current_user_followed_artists()
    for artist in followed['artists']['items']:
        artists.add(artist['name'])
    return artists

def create_playlist(spotipy, user_id, name_playlist):
    """
    Function that will create a playlist por a user
    with name provided
    user_id = current_user['id']
    """
    spotipy.user_playlist_create(user_id, name_playlist, public=True)
    print 'playlist created'


def add_songs_to_playlist(spotipy, user_id, playlist_id, id_songs):
    """
    add songs to a playlist providing user, id playlist
    and a list of songs
    """
    spotipy.user_playlist_add_tracks(user_id, playlist_id, id_songs)
    print 'track added to playlist'


def get_id_from_playlist(spotipy, name_playlist):
    """
    function that return the id of a playlist
    providing the id
    """
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


def random_catalog(artists, limit=15):
    catalog = Catalog('your_catalog', 'general')
    artists = list(artists)
    for _ in xrange(limit):
        choice = random.choice(artists)
        insert_to_catalog(catalog, choice)
    return catalog


def seed_playlist(catalog):
    pl = playlist.static(type='artist-radio', seed_catalog=catalog, results=50)
    catalog.delete()
    return pl

