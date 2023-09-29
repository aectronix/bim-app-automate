import math
import os
import re
import uuid

from .db import DB
from .journal import RevitJournal
from .system import System

config = {
	'usr_dir': '\\C$\\Users',
	'rvt_dir': '\\AppData\\Local\\Autodesk\\Revit',
	'jrn_dir': 'Journals',
	'filters': {
		'user': ['All Users', 'archadm', 'Default', 'Default User', 'Public', 'Администратор', 'Все пользователи']
	}
}

class CDE (System):

	def __init__(self, host: str):

		self.host = host
		self.user_dirs = None

		self.getUserDirs()


	def getUserDirs(self):

		usr_dir = self.host + config['usr_dir']
		user_dirs = [os.path.join(usr_dir, d) for d in os.listdir(usr_dir) if not d in config['filters']['user']]
		user_dirs = [d for d in user_dirs if os.path.isdir(d)]

		self.user_dirs = user_dirs


	def getJournals(self, bSync = True):

		paths = list()
		for ud in self.user_dirs:
			path = ud + config['rvt_dir']

			if os.path.isdir(path):
				version = [os.path.join(path, directory) for directory in os.listdir(path) if 'Autodesk Revit 20' in directory]
				for v in version:
					vpath = os.path.join(v, config['jrn_dir'])
					if os.path.isdir(vpath):

						for j in os.listdir(vpath):

							if re.match(r'.*\.txt$', j):

								jpath = os.path.join(vpath, j)
								mtime = math.floor(os.path.getmtime(os.path.join(vpath, j)))

								db = DB()
								query = db.cursor.execute('SELECT id, mtime, name, path FROM journals WHERE name = ? AND path = ?', (j, jpath))
								row = query.fetchone()

								if row:
									jid = row[0]
									if bSync:
										if mtime > row[1]:
											paths.append({'id': jid, 'path': jpath})
										else:
											pass

								else:
									jid = None
									paths.append({'id': jid, 'path': jpath})


								# jid = row[0] if row else None
								# if not dbsync or not row or (dbsync, row and mtime > row[1]):
								# 	paths.append({'id': jid, 'path': jpath})


					else: print('No journal folder found')

			else: print('No Revit folder found')

		if not paths: print('No journals found or there are any new journals')

		return paths

	# TODO: filter journals by modification datetime

	def getJournalsData(self, journals: list):

		data = [RevitJournal(j['id'], j['path']) for j in journals]

		return data