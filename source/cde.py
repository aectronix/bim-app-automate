import math
import os
import re
import uuid

from .journal import RevitJournal

config = {
	'usr_dir': '\\C$\\Users',
	'rvt_dir': '\\AppData\\Local\\Autodesk\\Revit',
	'jrn_dir': 'Journals',
	'filters': {
		'user': ['All Users', 'archadm', 'Default', 'Default User', 'Public', 'Администратор', 'Все пользователи']
	}
}

class CDE:

	#__slots__ = ['host', 'user_dirs']

	def __init__(self, host: str, db):

		self.host = host
		self.user_dirs = None

		self.db = db

		self.getUserDirs()


	def getUserDirs(self):

		usr_dir = self.host + config['usr_dir']
		user_dirs = [os.path.join(usr_dir, d) for d in os.listdir(usr_dir) if not d in config['filters']['user']]
		user_dirs = [d for d in user_dirs if os.path.isdir(d)]

		self.user_dirs = user_dirs


	def getJournals(self):

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

								# parse journals, pick up only new and modified
								jpath = os.path.join(vpath, j)
								mtime = math.floor(os.path.getmtime(os.path.join(vpath, j)))
								c = self.db.dbcon.cursor()
								q = c.execute('SELECT id, mtime, name, path FROM journals WHERE name = ? AND path = ? AND mtime = ?', (j, jpath, mtime))
								r = q.fetchone()

								if not r:
									jid = str(uuid.uuid4())
									paths.append({'id': jid, 'path': jpath})
									self.db.addJournalItem(jid, mtime, j, jpath)

								elif mtime > r[1]:
									q = c.execute('UPDATE journals SET mtime = ? WHERE id = ?', (mtime, r[0]))
									paths.append({'id': r[0], 'path': jpath})


					else: print('No journal folder found')

			else: print('No Revit folder found')

		if not paths: print('No journals found or there are any new journals')

		return paths

	# TODO: filter journals by modification datetime

	def getJournalsData(self, journals: list):

		data = [RevitJournal(j['id'], j['path']) for j in journals]
		
		return data