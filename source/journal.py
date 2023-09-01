import os
import re

from datetime import datetime

commands = [
	{ 'open': r'Jrn\.RibbonEvent.*ModelBrowserOpenDocumentEvent:open:.*modelGuid.*' },
	{ 'open': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_OPEN|.*ID_APPMENU_PROJECT_OPEN).*' },
	{ 'save': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_SAVE|.*ID_REVIT_FILE_SAVE_AS|.*ID_REVIT_SAVE_AS_TEMPLATE).*' },
	{ 'sync': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_FILE_SAVE_TO_CENTRAL|.*ID_FILE_SAVE_TO_MASTER_SHORTCUT).*' },
	{ 'exit': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_CLOSE|.*ID_APP_EXIT).*' },
]

schemes = {
	'cloud': r'""displayName"":""(.*?)"",',
	'onsave': r'\[ISL\] On save.*Adler Checksum:.*\[(.*?)\]',
	'init': r'Server-based Central Model \[identity.*?path = "(.*?)"]: init',
	'idok': r'\s*"IDOK"\s*,\s*"([^"]*)"',
	'info': r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing:.*Rvt\.Attr\.LastSavePath: (.*?) Rvt\.Attr\.LTProject:',
	'ws': r'\s*\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.Username:.*Rvt\.Attr\.LTProject:',
	'modsave': r'\s*\[Jrn\.ModelOperation\].*Rvt\.Attr\.Scenario: ModelSave.*Rvt.Attr.Worksharing: (.*?) Rvt\.Attr\.ModelState:',
	'savecloud': r'\s*Jrn\.AddInEvent.*WpfWindow(SaveAsCloudModelWindow,(.*?)).WpfSaveAsCloudModelBrowser',
}

class RevitJournal:

	__slots__ = ['name', 'path', 'build', 'data']

	def __init__(self, path: str):

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

				# try to catch the commands
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

				# TODO:
				#' 0:< Autodesk.Bcg.Http.HttpRequestStatusException: Forbidden: Unknown response GetModelResponse 
				#'C 01-Sep-2023 18:07:12.846;   0:< HttpRequestFailedException "403" "Forbidden: Unknown response GetModelResponse" 

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

							open_file = self._get_cmd_file([schemes['cloud'], schemes['idok']], l)
							if open_file: cmd['file'] = open_file

					elif cmd['cmd'] == 'save':
						if not 'file' in cmd:

							save_file = self._get_cmd_file([schemes['onsave'], schemes['init'], schemes['idok']], l)
							if save_file: cmd['file'] = save_file

					elif cmd['cmd'] == 'sync':
						if not 'file' in cmd:

							sync_file = self._get_cmd_file([schemes['init'], schemes['info']], l)
							if sync_file: cmd['file'] = sync_file

					# worksharing state
					if 'file' in cmd and not 'status' in cmd:
						status = self._get_cmd_status([schemes['ws'], schemes['modsave'], schemes['savecloud']], l)
						if status: cmd['status'] = status

				li += 1


		# just for case
		if self.data['ops'] and not 'file' in self.data['ops'][-1]:
			del self.data['ops'][-1]


	# extrat data from specific scheme parts
	@staticmethod
	def _get_cmd_file(schemes, line):
		for s in schemes:
			q = re.search(s, line)
			if q and q.group(1):
				if '/' in q.group(1) or '\\' in q.group(1):
					file = re.search(r'[\\/](?=[^\\/]*$)(.+)$', q.group(1))
					return file.group(1)
				else:
					return q.group(1)
				break

	@staticmethod
	def _get_cmd_status(schemes, line):
		for s in schemes:
			q = re.search(s, line)
			if q and q.group(1):
				return q.group(1)
				break