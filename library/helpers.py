import spotipy
import spotipy.util as util


def get_user_saved_tracks(spotipy):
    """
    return a set with the saved tracks.
    for now it will return a set with only the artists
    """
    offset = 0
    tracks = set()
    artists = set()  # this set will be deleted if later we returns tracks instead of artists
    while True:
        albums = spotipy.current_user_saved_tracks(limit=50, offset=offset)
        if not albums['items']:
            break
        for item in albums['items']:
            track = item['track']
            tracks.add(track['name'])
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
    playlist_artists = set()
    offset = 0
    user_id = spotipy.current_user()['id']
    playlists = spotipy.user_playlists(user_id)
    for playlist in playlists['items']:
        results = spotipy.user_playlist(user_id, playlist['id'], fields="tracks,next")
        tracks = results['tracks']
        show_tracks(tracks)
        while tracks['next']:
            tracks = sp.next(tracks)
    return set(playlist_artists_list)


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
