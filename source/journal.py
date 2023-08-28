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

		commands = [
			{ 'open': r'^\s*Jrn\.Command\s+".*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_OPEN|.*ID_APPMENU_PROJECT_OPEN).*' },
			{ 'open': r'^\s*Jrn\.RibbonEvent\s+".*ModelBrowserOpenDocumentEvent:open:.*modelGuid"".*' },
			{ 'save': r'^\s*Jrn\.Command\s+".*(?=Ribbon|Internal|AccelKey").*Save the active project.*' },
			#{ 'save': r'sync' },
		]

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
				for c in commands:
					if re.search(c[next(iter(c))], l):
						# q = re.search(c[next(iter(c))], l)
						# print(q.group())
						if len(self.data['ops']) > 0 and not 'file' in self.data['ops'][-1]:
							del self.data['ops'][-1]
						self.data['ops'].append({'idx': li, 'cmd': next(iter(c))})
						# print(self.data['ops'][-1])
						break

				# cancellation
				if len(self.data['ops']) > 0 and re.search(r'\s*,\s*"IDCANCEL"\s*', l):
					if not 'file' in self.data['ops'][-1]:
						del self.data['ops'][-1]

				# open
				if len(self.data['ops']) > 0:
					cmd = self.data['ops'][-1] # last cmd entry

					if cmd['cmd'] == 'open':
						# cloud
						cloud_file = re.search(r'""displayName"":""(.*?)"",', l)
						if cloud_file:
							date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
							if date:
								cmd['date'] = date.group(0)
								cmd['file'] = cloud_file.group(1)
								
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
						share = re.search(r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.Username:.*Rvt\.Attr\.LTProject:', l)
						if share and share.group(1):
							path = re.search(r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing:.*Rvt\.Attr\.LastSavePath: (.*?) Rvt\.Attr\.LTProject:', l)
							if path and path.group(1):
								cmd['share'] = share.group(1)

				li += 1


		# just for case
		if len(self.data['ops']) > 0 and not 'file' in self.data['ops'][-1]:
			del self.data['ops'][-1]