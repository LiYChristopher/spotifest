WTF_CSRF_ENABLED = True
SECRET_KEY = 'default_key_to_change'

import re

class DefaultConfig(object):

	creds = {}
	with open('credentials.txt', 'r') as cred:
		for i in cred.readlines():
			read = re.search(r'(\w+):(.+)', i,re.I)
			creds[read.group(0)] = read.groups(1)
	print creds
	def __init__(self):
		pass
