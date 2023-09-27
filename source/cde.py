import os
import re

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

	__slots__ = ['host', 'user_dirs']

	def __init__(self, host: str):

		self.host = host
		self.user_dirs = None

		self.getUserDirs()


	def getUserDirs(self):

		usr_dir = self.host + config['usr_dir']
		user_dirs = [os.path.join(usr_dir, d) for d in os.listdir(usr_dir) if not d in config['filters']['user']]
		user_dirs = [d for d in user_dirs if os.path.isdir(d)]

		self.user_dirs = user_dirs


	def getJournals(self, filter = True):

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
								mtime = os.path.getmtime(os.path.join(vpath, j))
								if mtime >= 1693834568:											# TODO: change to base
									paths.append(os.path.join(vpath, j))

					else: print('No Autodesk Revit journal folder found')

			else: print('No Autodesk Revit folder found')

		if not paths: print('No Autodesk Revit journals found:')

		return paths

	# TODO: filter journals by modification datetime

	def getJournalsData(self, pathlist: list):

		data = [RevitJournal(j) for j in pathlist]
		
		return data