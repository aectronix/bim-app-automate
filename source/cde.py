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

	__slots__ = ['host', 'usr_dirs', 'journals']

	def __init__(self, host: str):

		self.host = host
		self.usr_dirs = None
		self.journals = None

		self.getHostUsers()
		self.getJournalPaths()
		# self.getJournalData()


	def getHostUsers(self):

		usr_dir = self.host + config['usr_dir']
		usr_dirs = [os.path.join(usr_dir, d) for d in os.listdir(usr_dir) if not d in config['filters']['user']]
		usr_dirs = [d for d in usr_dirs if os.path.isdir(d)]

		self.usr_dirs = usr_dirs


	def getJournalPaths(self):

		paths = list()
		for ud in self.usr_dirs:
			path = ud + config['rvt_dir']

			if os.path.isdir(path):
				version = [os.path.join(path, directory) for directory in os.listdir(path) if 'Autodesk Revit 20' in directory]
				for v in version:
					jpath = os.path.join(v, config['jrn_dir'])
					if os.path.isdir(jpath):
						journals = [j for j in os.listdir(jpath) if re.match(r'.*\.txt$', j)]
						paths += [os.path.join(jpath, j) for j in journals]
					else: print("No Autodesk Revit journal folder found:(")

			else: print("No Autodesk Revit folder found:(")

		if not paths: print("No Autodesk Revit journals found:(")

		self.journals = paths

	# TODO: filter journals by modification datetime

	def getJournalProp(self):

		print('journal sys info')


	def getJournalData(self):

		data = [RevitJournal(j) for j in self.journals]
		
		return data