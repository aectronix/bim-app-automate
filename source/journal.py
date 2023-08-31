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

		schemes = {
			'onsave': r'\[ISL\] On save.*Adler Checksum:.*\[(.*?)\]',
			'init': r'Server-based Central Model \[identity.*?path = "(.*?)"]: init',
			'idok': r'\s*"IDOK"\s*,\s*"([^"]*)"',
			'cloud': r'""displayName"":""(.*?)"",',
			'info': r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing:.*Rvt\.Attr\.LastSavePath: (.*?) Rvt\.Attr\.LTProject:',
		}

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
						if self.data['ops'] and not 'file' in self.data['ops'][-1]:
							del self.data['ops'][-1]
						date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[li-2])
						self.data['ops'].append({'idx': li, 'cmd': next(iter(c)), 'date': date.group(0)})
						break

				# cancellation by ui
				if self.data['ops'] and re.search(r'\s*,\s*"IDCANCEL"\s*', l):
					if not 'file' in self.data['ops'][-1]:
						del self.data['ops'][-1]

				# command cases
				if self.data['ops']:
					cmd = self.data['ops'][-1] # last cmd entry

					# transform exit commands into the final ones
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
						if not 'file' in cmd:
							for s in [schemes['cloud'], schemes['idok']]:
								save_file = self._get_file_data(s, l)
								if save_file: cmd['file'] = save_file

					if cmd['cmd'] == 'save':
						if not 'file' in cmd:

							for s in [schemes['onsave'], schemes['init'], schemes['idok']]:
								save_file = self._get_file_data(s, l)
								if save_file: cmd['file'] = save_file
						# TODO:
						# else:
						# 	q3 = re.search(r'\s*\[Jrn\.ModelOperation\].*Rvt\.Attr\.Scenario: ModelSave.*Rvt.Attr.Worksharing: (.*?) Rvt\.Attr\.ModelState:',l)
						# 	if q3:
						# 		cmd['status'] = q3.group(1)
							# if re.search(r'\s*SLOG.*>SaveAsCentral.*', l):
							# 	if 'RSN' in q2.group():
							# 		cmd['status'] = 'RevitServer Central'
							# 	else:
							# 		cmd['status'] = 'File-Based Central'

					if cmd['cmd'] == 'sync':
						if not 'file' in cmd:

							for s in [schemes['init'], schemes['info']]:
								save_file = self._get_file_data(s, l)
								if save_file: cmd['file'] = save_file

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
		if self.data['ops'] and not 'file' in self.data['ops'][-1]:
			del self.data['ops'][-1]

	@staticmethod
	def _get_file_data(query, line):
		q = re.search(query, line)
		if q:
			if '/' in q.group(1) or '\\' in q.group(1):
				file = re.search(r'[\\/](?=[^\\/]*$)(.+)$', q.group(1))
				return file.group(1)
			else:
				return q.group(1)
				