import spotipy
import spotipy.util as util

from pyechonest import config
from pyechonest import playlist
from pyechonest.catalog import Catalog
from library.app import celery


import random

config.ECHO_NEST_API_KEY = "SNRNTTK9UXTWYCMBH"





@celery.task(name='saved_tracks')
def get_user_saved_tracks(spotipy):
    '''
    return a set with the saved tracks.
    for now it will return a set with only the artists
    '''
    offset = 0  # this set will be deleted if later we returns tracks instead of artists
    while True:
        albums = spotipy.current_user_saved_tracks(limit=50, offset=offset)
        if not albums['items']:
            break
        artists = {item['track']['artists'][0]['name']
                    for item in albums['items']}
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
    for artist in followed['artists']['items']:
        artists = {artist['name'] for artist in followed['artists']['items']}
    return artists


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


@celery.task(name='song_ids')
def get_songs_id(spotipy, playlist, offset):
    '''
    get a list of sgons names and return list of songs ids
    '''
    songs_id = []
    for item in playlist[offset:offset+10]:
        q = "track:{} artist:{}".format(item.title.encode('utf-8'),
                                        item.artist_name.encode('utf-8'))
        result = spotipy.search(q, type='track', limit=1)
        if not result['tracks'].get('items'):
            continue
        spotify_id = spotipy.search(q, type='track', limit=1)['tracks']['items'][0]['id']
        songs_id.append(spotify_id)
    return songs_id
