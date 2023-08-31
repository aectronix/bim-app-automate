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
			{ 'save': r'^\s*Jrn\.Command\s+".*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_SAVE|.*ID_REVIT_FILE_SAVE_AS|.*ID_REVIT_SAVE_AS_TEMPLATE).*' },
			{ 'sync': r'^\s*Jrn\.Command\s+".*(?=Ribbon|Internal|AccelKey")(?=.*ID_FILE_SAVE_TO_CENTRAL|.*ID_FILE_SAVE_TO_MASTER_SHORTCUT).*' },
			{ 'exit': r'^\s*Jrn\.Command\s+".*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_CLOSE|.*ID_APP_EXIT).*' },
		]

		with open(self.path, 'r') as file:

			lines = file.readlines()
			li = 1

			for l in lines:

				# # builds
				# build = re.search(r"' Build:\s+(\S+)", l)
				# if build:
				# 	self.data['build'] = build.group(1)

				# # users
				# user = re.search(r'"Username"\s*,\s*"([^"]*)"', l)
				# if user:
				# 	self.data['user'] = user.group(1)

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

				# command cases
				if len(self.data['ops']) > 0:
					cmd = self.data['ops'][-1] # last cmd entry

					if cmd['cmd'] == 'exit':
						if re.search(r'\s*"TaskDialogResult".*',l):
							rows = (lines[li], lines[li+1])
							if any('Yes' in line for line in rows) and any('IDYES' in line for line in rows):
								cmd['cmd'] = 'save'
							elif any('Save to cloud' in line for line in rows) and any('1001' in line for line in rows):
								cmd['cmd'] = 'save'
							elif any('Synchronize with central' in line for line in rows) and any('1001' in line for line in rows):
								cmd['cmd'] = 'sync'

					if cmd['cmd'] == 'open':
						# cloud
						cloud_file = re.search(r'""displayName"":""(.*?)"",', l)
						if cloud_file:
							date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
							if date:
								cmd['date'] = date.group(0)
								cmd['file'] = cloud_file.group(1)
								
						# other
						f = re.search(r'\s*"IDOK"\s*,\s*"([^"]*)"', l)
						if f and f.group(1):
							date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
							fn = re.search(r'[\\/](?=[^\\/]*$)(.+)$', f.group(1))
							if fn and fn.group(1) and date:
								cmd['date'] = date.group(0)
								cmd['file'] = fn.group(1)

					if cmd['cmd'] == 'save':
						if not 'file' in cmd:
							q4 = re.search(r'\[ISL\] On save.*Adler Checksum:.*\[(.*?)\]', l)
							if q4:
								save_file = re.search(r'[\\/](?=[^\\/]*$)(.+)$', q4.group(1))
								save_date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
								if save_file and save_date:
									cmd['date'] = save_date.group(0)
									cmd['file'] = save_file.group(1)
							q1 = re.search(r'Server-based Central Model \[identity.*?path = "(.*?)"]: init', l)
							if q1:
								sync_file = re.search(r'[\\/](?=[^\\/]*$)(.+)$', q1.group(1))
								sync_date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
								if sync_file and sync_date:
									cmd['date'] = sync_date.group(0)
									cmd['file'] = sync_file.group(1)
							q2 = re.search(r'\s*"IDOK"\s*,\s*"([^"]*)"', l)
							if q2:
								sync_file = re.search(r'[\\/](?=[^\\/]*$)(.+)$', q2.group(1))
								sync_date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
								if sync_file and sync_date:
									cmd['date'] = sync_date.group(0)
									cmd['file'] = sync_file.group(1)
						else:
							q3 = re.search(r'\s*\[Jrn\.ModelOperation\].*Rvt\.Attr\.Scenario: ModelSave.*Rvt.Attr.Worksharing: (.*?) Rvt\.Attr\.ModelState:',l)
							if q3:
								cmd['status'] = q3.group(1)
							if re.search(r'\s*SLOG.*>SaveAsCentral.*', l):
								if 'RSN' in q2.group():
									cmd['status'] = 'RevitServer Central'
								else:
									cmd['status'] = 'File-Based Central'

					if cmd['cmd'] == 'sync':
						if not 'file' in cmd:
							# Retrieving from such lines: Server-based Central Model [identity = 61ff9ecf-148d-462a-81d9-94e7e895cd26, region = "US", path ...
							q1 = re.search(r'Server-based Central Model \[identity.*?path = "(.*?)"]: init', l)
							if q1:
								sync_file = re.search(r'[\\/](?=[^\\/]*$)(.+)$', q1.group(1))
								sync_date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
								if sync_file and sync_date:
									cmd['date'] = sync_date.group(0)
									cmd['file'] = sync_file.group(1)
							# Retrieving from such lines: [Jrn.BasicFileInfo] Rvt.Attr.Worksharing: ...
							q2 = re.search(r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing:.*Rvt\.Attr\.LastSavePath: (.*?) Rvt\.Attr\.LTProject:', l)
							if q2:
								sync_file = re.search(r'[\\/](?=[^\\/]*$)(.+)$', q2.group(1))
								sync_date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[cmd['idx']-2])
								if sync_file and sync_date:
									cmd['date'] = sync_date.group(0)
									cmd['file'] = sync_file.group(1)

					# worksharing state
					if 'file' in cmd and not 'status' in cmd:
						if 'ID_REVIT_FILE_SAVE_AS_CLOUD_MODEL' in lines[cmd['idx']-1]:
							cmd['status'] = 'Nonworkshared Cloud Local'

						status = re.search(r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.Username:.*Rvt\.Attr\.LTProject:', l)
						if status and status.group(1):
							path = re.search(r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing:.*Rvt\.Attr\.LastSavePath: (.*?) Rvt\.Attr\.LTProject:', l)
							if path and path.group(1):
								cmd['status'] = status.group(1)

				li += 1


		# just for case
		if len(self.data['ops']) > 0 and not 'file' in self.data['ops'][-1]:
			del self.data['ops'][-1]