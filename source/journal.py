import os
import re

from datetime import datetime

class RevitJournal:

	__slots__ = ['name', 'path', 'build', 'data']

	def __init__(self, path):

		self.path = path
		self.data = {
			'name':  os.path.basename(path),
			# 'path': path,
			'build': None,
			'user': None,
			'ops': {
				'open': []
			}
		}

		self.getJournalData()

	def getJournalData(self):

		with open(self.path, 'r') as file:

			lines = file.readlines()
			li = 1

			for l in lines:

				# builds
				build = re.search(r"' Build:\s+(\S+)", l)
				if build:
					self.data['build'] = build.group(1)

				# users
				user = re.search(r'"Username"\s*,\s*"([^"]*)"', l)
				if user:
					self.data['user'] = user.group(1)

				# operations
				if len(self.data['ops']['open']) > 0:
					c = re.search(r'^\s*Jrn\.Command\s+".*(?=Ribbon|Internal|AccelKey").*', l)
					if c:
						if not 'file' in self.data['ops']['open'][-1]:
							del self.data['ops']['open'][-1]
						if 'ID_REVIT_FILE_OPEN' in c.group() or 'ID_APPMENU_PROJECT_OPEN' in c.group():
							self.data['ops']['open'].append({'idx': li})

					# cancellation
					cancel = re.search(r'\s*,\s*"IDCANCEL"\s*', l)
					if cancel:
						if len(self.data['ops']['open']) > 0 and not 'file' in self.data['ops']['open'][-1]:
							del self.data['ops']['open'][-1]

				else:
					if re.search(r'^\s*Jrn\.Command\s+".*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_OPEN|.*ID_APPMENU_PROJECT_OPEN).*', l):
						self.data['ops']['open'].append({'idx': li})

				# todo: ID_FILE_OPEN_CLOUD

				# open
				if len(self.data['ops']['open']) > 0:
					cmd = self.data['ops']['open'][-1]
					f = re.search(r'\s*"IDOK"\s*,\s*"([^"]*)"', l)

					if f and f.group(1):
						dt = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
						fn = re.search(r'[\\/](?=[^\\/]*$)(.+)$', f.group(1))
						if fn and fn.group(1) and dt:
							cmd['date'] = dt.group(0)
							cmd['file'] = fn.group(1)
							if 'RSN' in f.group(1):
								cmd['host'] = 'server'

					if 'file' in cmd:
						if not 'host' in cmd:
							cm = re.search(r'\s*SLOG\s*central\s*=\s*\".*[\\/]([^\"/]+)\"', l)
							if cm and cm.group(1) == cmd['file']:
								cmd['host'] = 'network'

				li += 1


		# just for case
		if len(self.data['ops']['open']) > 0 and not 'file' in self.data['ops']['open'][-1]:
			del self.data['ops']['open'][-1]