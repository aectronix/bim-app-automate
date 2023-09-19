import os
import re

from datetime import datetime

# The bunch of schemes to extract the primary command
commands = [
	# { 'open': r'Jrn\.RibbonEvent.*ModelBrowserOpenDocumentEvent:open:.*modelGuid.*' },
	# { 'open': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_OPEN|.*ID_APPMENU_PROJECT_OPEN|.*ID_FAMILY_OPEN|.*ID_IMPORT_IFC).*' },
	# { 'save': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_SAVE|.*ID_REVIT_FILE_SAVE_AS|.*ID_REVIT_SAVE_AS_TEMPLATE|.*ID_SAVE_FAMILY|.*ID_REVIT_SAVE_AS_FAMILY).*' },
	# { 'sync': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_FILE_SAVE_TO_CENTRAL|.*ID_FILE_SAVE_TO_MASTER_SHORTCUT|.*ID_COLLABORATE).*' },
	# { 'exit': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_CLOSE|.*ID_APP_EXIT).*' },
	{ 'exit': r'Jrn\.Command\s+".*,\s(ID_REVIT_FILE_CLOSE|ID_APP_EXIT)"' },
	{ 'open': r'Jrn\.Command\s+".*,\s(ID_REVIT_FILE_OPEN|ID_APPMENU_PROJECT_OPEN|ID_FAMILY_OPEN|ID_IMPORT_IFC)"' },
	{ 'save': r'Jrn\.Command\s+".*,\s(ID_REVIT_FILE_SAVE|ID_REVIT_FILE_SAVE_AS|ID_REVIT_SAVE_AS_TEMPLATE|ID_SAVE_FAMILY|ID_REVIT_SAVE_AS_FAMILY)"' },
	{ 'sync': r'Jrn\.Command\s+".*,\s(ID_FILE_SAVE_TO_CENTRAL|ID_FILE_SAVE_TO_MASTER_SHORTCUT|ID_COLLABORATE)"' },
]

# The bunch of schemes to extract the command data
schemes = {

	# uuid
	'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',

	# separate file from path
	'file': r'[\\/](?=[^\\/]*$)(.+)$',

	'detect': { 'pattern': r'Detect if missing elements for (.*?): File Size: (-?\d+), Element Count: \d+', 'items': ['file', 'size'] },
	
	'idok': { 'pattern': r'"IDOK"\s*,\s*"([^"]*)"', 'items': ['file'] },

	'fsizecomp': { 'pattern': r'FileSizeComparison.*\)".*\b(\d+)\b', 'items': ['size'] },
	
	'skybase_size': { 'pattern': r'skybase_model_size_bytes:.*\b(\d+)\b', 'items': ['size'] },

	'fileinfo': { 'pattern': r'\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.Username:.*Rvt\.Attr\.CentralModelPath: (.*?) Rvt.Attr.RevitBuildVersion:.*Rvt\.Attr\.LastSavePath:(.*?) Rvt\.Attr\.LTProject:', 'items': ['status', 'file', 'file'] },

	'filesizeopen': { 'pattern': r'fileSizeOnOpen:(\d+)KB', 'items': ['size'] },

	'saveas': { 'pattern': r'SLOG .* >(\w+)  "(.*?)"', 'items': ['status', 'file'] },

	'modelsave': { 'pattern': r'Jrn\.ModelOperation.*Rvt\.Attr\.Scenario.*ModelSave.*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.ModelState:', 'items': ['status'] },

	# Command process is interrupted by user pushing the ui button:
	# >>> 'H 29-Aug-2023 23:58:27.246;   0:< Jrn.Data  _ "File Name"  , "IDCANCEL" , "" 
	'cancel': r'IDCANCEL',

	'cancel_cloud': r'AddInJournaling.*WpfButton\(0,CancelButton\)\.Click',

	# Request status is unknown (cloud cases):
	# >>> 0:< Autodesk.Bcg.Http.HttpRequestStatusException: Forbidden: Unknown response GetModelResponse 
	'request_unknown': r'HttpRequestStatusException.*Unknown response.*GetModelResponse.*',
	# Requestis failed, access is forbidden (cloud case):
	# >>> C 01-Sep-2023 18:07:12.846; 0:< HttpRequestFailedException "403" "Forbidden: Unknown response GetModelResponse" 
	'request_failed': r'HttpRequestFailedException.*403.*Forbidden.*',

	# 'detect': r'Detect if missing elements for (.*?): File Size: (\d+), Element Count: \d+',
}



class RevitJournal:

	__slots__ = ['name', 'path', 'build', 'data']

	def __init__(self, path: str):

		self.path = path
		self.data = {
			'name':  os.path.basename(path),
			'path': path,
			'build': None,
			'user': None,
			'ops': []
		}

		self.getJournalData()

	def getJournalData(self):

		with open(self.path, 'r') as file:

			lines = file.readlines()
			li = 0

			for l in lines[:-1]:

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
					command = re.search(c[next(iter(c))], l)
					if command:
						# if self.data['ops'] and not 'file' in self.data['ops'][-1]:
						# 	del self.data['ops'][-1]
						date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[li-1])
						self.data['ops'].append({'idx': li+1, 'type': next(iter(c)), 'command': command.group(1), 'date': date.group(0)})
						break

				# get the ast entry if exists
				if self.data['ops']:
					cmd = self.data['ops'][-1]

					# cancellation & del
					if (self._get_cmd_stop([schemes['cancel']], l) and not 'file' in cmd) or self._get_cmd_stop([schemes['cancel_cloud'], schemes['request_unknown'], schemes['request_failed']], l):
						del self.data['ops'][-1]

					# transform exit commands into the final ones
					if cmd['type'] == 'exit':
						if re.search(r'\s*"TaskDialogResult".*', l):
							rows = (lines[li], lines[li+1])
							if any('Yes' in line for line in rows) and any('IDYES' in line for line in rows):
								cmd['cmd'] = 'save'
							elif any('Save to cloud' in line for line in rows) and any('1001' in line for line in rows):
								cmd['cmd'] = 'save'
							elif any('Synchronize with central' in line for line in rows) and any('1001' in line for line in rows):
								cmd['cmd'] = 'sync'

					if not 'file' in cmd:
						data = self._parse_by_scheme([schemes['idok'], schemes['detect'], schemes['fileinfo']], l)
						for d in data:
							if not d in cmd:
								cmd[d] = data[d]

					if not 'size' in cmd:
						data = self._parse_by_scheme([schemes['fsizecomp'], schemes['filesizeopen'], schemes['skybase_size'], schemes['detect']], re.sub(r'\s+', ' ', l + lines[li+1]))
						for d in data:
							if not d in cmd:
								cmd[d] = data[d]

					if not 'status' in cmd:
						data = self._parse_by_scheme([schemes['fileinfo'], schemes['saveas'], schemes['modelsave']], l)
						for d in data:
							if not d in cmd:
								cmd[d] = data[d]

				li += 1


		# just for case
		# if self.data['ops'] and not 'file' in self.data['ops'][-1]:
		# 	del self.data['ops'][-1]


	# extrat data from specific scheme parts
	@staticmethod
	def _get_cmd_stop(schemes, line):
		for s in schemes:
			q = re.search(s, line)
			if q:
				return True
				break

	@staticmethod
	def _parse_by_scheme(schemlist, line):
		result = {}
		for s in schemlist:
			q = re.search(s['pattern'], line)
			if q:
				for i in range(len(s['items'])):

					if s['items'][i] == 'file':
						result['path'] = q.group(i+1)
						file = re.search(schemes['file'], q.group(i+1))
						if file and not re.match(schemes['uuid'], file.group(1)):
							result['file'] = file.group(1)
						else:
							pass

					else:
						result[s['items'][i]] = q.group(i+1)
				break
		return result
