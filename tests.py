from mock import Mock, patch
from flask import request, url_for, redirect, session
import unittest
import library
import os
import json


class HelperTests(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		class Spotipy(object):

			def __init__(self, test_dir_name):
				self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         test_dir_name)

			def current_user(self):
				return {'id': u'12345678'}

			def current_user_saved_tracks(self, limit=50, offset=0):
				with open(os.path.join(self.path, 'get_user_saved_tracks.json'), 'r') as data:
					d = json.load(data)
					d['items'] = d['items'][offset:offset + limit]
					return d

			def current_user_followed_artists(self):
				with open(os.path.join(self.path, 'get_followed_artists.json'), 'r') as data:
					d = json.load(data)
					return d

			def user_playlists(self, spotipy):
				with open(os.path.join(self.path, 'get_user_playlists.json'), 'r') as data:
					d = json.load(data)
					return d

			def user_playlist(self, owner, playlist, fields):
				with open(os.path.join(self.path, 'user_playlist.json'), 'r') as data:
					d = json.load(data)
					return d

		mock_attributes = Spotipy('testing')
		mock_spotipy = Mock(return_value=mock_attributes)
		cls.spotipy = mock_spotipy()
		return

	@classmethod
	def tearDownClass(cls):
		del cls.spotipy
		return

	def test_get_user_saved_tracks(self):
		''' helpers.get_user_saved_tracks(spotipy)'''
		res = library.helpers.get_user_saved_tracks(self.spotipy)
		return self.assertEqual(res, set([u'DJ Shadow', u'Red Hot Chili Peppers', u'Hermitude']))

	def test_get_user_playlists(self):
		''' helpers.get_user_playlists(spotipy) '''
		res = library.helpers.get_user_playlists(self.spotipy)
		return self.assertEqual(res, set([u'Scars On Broadway', u'Downset', u'Red Hot Chili Peppers',
			                             u'Snot', u'Bloodhound Gang', u"Jane's Addiction", u'CKY',
			                             u'One Minute Silence', u'Korn', u'Body Count',
			                             u'Living Colour', u'Primer 55', u'24-7 Spyz',
			                             u'Limp Bizkit', u'Tom Morello', u'Deftones',
			                             u'Faith No More', u'Primus', u'System of a Down',
			                             u'Slipknot', u'Linkin Park', u'One Day As A Lion',
			                             u'Street Sweeper Social Club', u'Audioslave',
			                             u'Alice In Chains', u'Fishbone', u'(Hed) P.E.',
			                             u'Incubus', u'Rage Against The Machine']))

	def test_get_user_followed(self):
		'''helpers.get_user_followed(spotipy)'''
		res = library.helpers.get_user_followed(self.spotipy)
		return self.assertEqual(res, set([u'David Bowie', u'Sun Glitters', u'Drake',
			                              u'Tori Kelly', u'Beacon', u'BadBadNotGood']))

	def test_get_id_from_playlist(self):
		''' helpers.get_id_from_playlist(spotipy, user_id, name_playlist)'''
		res = library.helpers.get_id_from_playlist(self.spotipy, 'festify_test', 'test_1')
		return self.assertEqual(res, '0IMs1kZrxMGyohDSXVVrAR')

	def test_process_to_item(self):
		''' helpers.process_to_item(artist) '''
		res = library.helpers.process_to_item('Paul McCartney')
		self.assertTrue(len(res), 1)
		self.assertTrue(res[0].get('action'))
		self.assertTrue(res[0].get('item'))
		self.assertTrue(res[0]['item'].get('artist_name') == 'Paul McCartney')
		return


class AuthTests(unittest.TestCase):

	config = {'client_id.return_value': '7c931eb8a9864d75aaaacb111a9f8d08',
			  'redirect_uri.return_value': 'http://google.com'}

	@classmethod
	@patch('library.db', autospec=True)
	def setUpClass(cls, db):
		cls.db = db
		cls.db.save_to_database.return_value = None
		cls.db.get_parameters.return_value = [0.5]*5
		cls.db.get_info_from_database.return_value = [99, 'Best Fest 2016', 'spotifester',
		                                              None, None, None]
		library.app.config['IS_ASYNC'] = False
		library.app.config['TESTING'] = True
		with library.app.app_context():
			cls.app = library.app.test_client()
 		return

	@classmethod
	def tearDownClass(cls):
		del cls.app
		return

	@patch('library.auth.oauth',  autospec=True, **config)
	def test_login(self, oauth):
		''' auth.login(config=BaseConfig, oauth=oauth)'''
		self.oauth = oauth
		self.oauth.OAUTH_AUTHORIZE_URL = 'https://accounts.spotify.com/authorize'
		self.oauth.client_id = 'test_client_id'
		self.oauth.redirect_uri = 'test_redirect_uri'
		self.oauth.scope = ['user-library-read', 'playlist-read-collaborative',
         					'user-follow-read', 'playlist-modify-public']
		res = library.auth.login(oauth=self.oauth)
		self.assertEqual(res, "https://accounts.spotify.com/authorize?"
			                  "scope=user-library-read&"
			                  "scope=playlist-read-collaborative&scope=user-follow-read&" 
			                  "scope=playlist-modify-public&redirect_uri=test_redirect_uri&"
			                  "response_type=code&client_id=test_client_id")
		del self.oauth

	def test_join_not_logged_in(self):
		''' @app.route('/festival/join/<url_slug>', methods=['GET'])
			@login_required
			def join(url_slug)'''

		with library.app.test_request_context('/festival/join/FFFFF'):
			res = self.app.get(url_for('join', url_slug='FFFFF'),
				               follow_redirects=False)
			self.assertEqual(res.status_code, 200)

	def test_server_home_logged_in(self):
		''' SERVER FUNCTIONALITY @app.route('/', methods=['POST', 'GET'])
			@app.route('/home', methods=['POST', 'GET'])
			def home(config=BaseConfig)'''
		# need to figure out efficient way to handle session transactions
		# or better way of handling logins
		return

	def test_template_home_not_logged_in(self):
		''' FRONTEND CONTENT @app.route('/', methods=['POST', 'GET'])
			@app.route('/home', methods=['POST', 'GET'])
			def home(config=BaseConfig)'''
		status = self.app.get('/').status_code	
		content = self.app.get('/').get_data()
		# status code
		self.assertEqual(status, 200)
		# divs equal
		div_count = content.count('<div')
		div_close_count = content.count('</div>')    
		self.assertEqual(div_count, div_close_count)
		# OAuth in homepage
		self.assertIn("https://accounts.spotify.com/authorize?scope=playlist-modify-public"
			          "+playlist-read-collaborative+user-follow-read+user-library-read&amp;", content)
		return

	def test_template_festival_not_logged_in(self):
		''' FRONTEND CONTENT @app.route('/', methods=['POST', 'GET'])
			@app.route('/home', methods=['POST', 'GET'])
			def home(config=BaseConfig)'''
		status = self.app.get('/festival/2jkasf').status_code
		content = self.app.get('/festival/2jkasf').get_data()
		# status code
		self.assertEqual(status, 200)
		# divs equal
		div_count = content.count('<div')
		div_close_count = content.count('</div>')
		self.assertEqual(div_count, div_close_count)
		# Login message
		self.assertIn("Please login with your Spotify "
			          "account before continuing", content)
		return

	def test_about(self):
		''' @app.route('/about')
			def about()'''
		status = self.app.get('/about').status_code
		self.assertEqual(status, 200)
		return

if __name__ == '__main__':

	unittest.main()
