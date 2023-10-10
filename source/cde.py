import os
import re

from .journal import RevitJournal
from .system import System

class CDE (System):

	def __init__(self, host: str):

		self.host = host
		self.user_dirs = None

		self.getUserDirs()


	def getUserDirs(self):

		usr_dir = '\\\\' + self.host + self.config['cde']['usr_dir']
		user_dirs = [os.path.join(usr_dir, d) for d in os.listdir(usr_dir) if not d in self.config['cde']['filters']['users']]
		user_dirs = [d for d in user_dirs if os.path.isdir(d)]

		self.user_dirs = user_dirs


	def getJournals(self):

		paths = list()
		for ud in self.user_dirs:
			path = ud + self.config['cde']['rvt_dir']

			if os.path.isdir(path):
				version = [os.path.join(path, directory) for directory in os.listdir(path) if 'Autodesk Revit 20' in directory]

				for v in version:
					vpath = os.path.join(v, self.config['cde']['jrn_dir'])
					if os.path.isdir(vpath):
						paths += [os.path.join(vpath, j) for j in os.listdir(vpath) if re.match(r'.*\.txt$', j)]

					else: print('No journal folder found')

			else: print('No Revit folder found')

		if not paths: print('No journals found or there are any new journals')

		return paths


	def getJournalsData(self, journals: list):

		data = [RevitJournal(j['id'], j['path']) for j in journals]

		return data


