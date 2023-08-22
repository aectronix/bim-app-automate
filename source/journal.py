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
			# 'build': None,
			# 'user': None,
			'ops': []
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

				# todo: organize commands

				# operations
				if re.search(r'^\s*Jrn\.Command\s+".*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_OPEN|.*ID_APPMENU_PROJECT_OPEN).*', l) or re.search(r'Open Cloud Model Method.*Model Guid:.*', l):
					if len(self.data['ops']) > 0 and not 'file' in self.data['ops'][-1]:
						del self.data['ops'][-1]
					self.data['ops'].append({'idx': li, 'cmd': 'open'})

				# cancellation
				if len(self.data['ops']) > 0 and re.search(r'\s*,\s*"IDCANCEL"\s*', l):
					if not 'file' in self.data['ops'][-1]:
						del self.data['ops'][-1]

				# open
				if len(self.data['ops']) > 0:
					cmd = self.data['ops'][-1] # last cmd entry

					# cloud
					file_cloud = re.search(r'Open Cloud Model Method.*Model Guid:\s*([^\s,]+)', l)
					if file_cloud and file_cloud.group(1):
						guid = re.search(r'"modelGuid"":""(.*?)""', lines[li-2])
						if guid and guid.group(1) == file_cloud.group(1):
							name = re.search(r'""displayName"":""(.*?)"",', lines[li-2])
							date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-1])
							if name and name.group(1) and date:
								cmd['date'] = date.group(0)
								cmd['file'] = name.group(1)
							
					# regular
					f = re.search(r'\s*"IDOK"\s*,\s*"([^"]*)"', l)
					if f and f.group(1):
						date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
						fn = re.search(r'[\\/](?=[^\\/]*$)(.+)$', f.group(1))
						if fn and fn.group(1) and date:
							cmd['date'] = date.group(0)
							cmd['file'] = fn.group(1)

					# worksharing state
					if 'file' in cmd:
						sharing = re.search(r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.Username:', l)
						if sharing and sharing.group(1):
							cmd['share'] = sharing.group(1)
	
				li += 1


		# just for case
		if len(self.data['ops']) > 0 and not 'file' in self.data['ops'][-1]:
			del self.data['ops'][-1]