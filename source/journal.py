import os
import re

from datetime import datetime

# The bunch of schemes to extract the primary command
commands = [
	{ 'open': r'Jrn\.RibbonEvent.*ModelBrowserOpenDocumentEvent:open:.*modelGuid.*' },
	{ 'open': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_OPEN|.*ID_APPMENU_PROJECT_OPEN|.*ID_IMPORT_IFC).*' },
	{ 'save': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_SAVE|.*ID_REVIT_FILE_SAVE_AS|.*ID_REVIT_SAVE_AS_TEMPLATE).*' },
	{ 'sync': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_FILE_SAVE_TO_CENTRAL|.*ID_FILE_SAVE_TO_MASTER_SHORTCUT).*' },
	{ 'exit': r'Jrn\.Command.*(?=Ribbon|Internal|AccelKey")(?=.*ID_REVIT_FILE_CLOSE|.*ID_APP_EXIT).*' },
]

# The bunch of schemes to extract the command data
schemes = {
	# Retrieve the file for cloud models openings:
	# >>> Jrn.RibbonEvent "ModelBrowserOpenDocumentEvent:open:{""projectGuid"":""???"",""modelGuid"":""???"",""id"":""cld://US/{???}__SHA/{???}???"",""displayName"":""???"",""region"":""US"",""modelVersion"":""0""}" 
	'model_browser': r'""displayName"":""(.*?)"",',
	# Retrieve the file for local savings:
	# >>> 2:< [ISL] On save, Adler Checksum: 0x3dab8d16 [C:\Users\username\Desktop\???] 
	'onsave': r'\[ISL\] On save.*Adler Checksum:.*\[(.*?)\]',
	# Retrieve the file for save and synchronisation commands:
	# >>> Server-based Central Model [identity = ???, region = "US", path = "Autodesk Docs://__SHA/???"]: init
	'init': r'Server-based Central Model \[identity.*?path = "(.*?)"]: init',
	# Pretty common case for a lot of commands, also works like a confirmation:
	# >>> H 30-Aug-2023 00:37:11.806;   0:<  Jrn.Data  _ "File Name"  , "IDOK" , "???" 
	'idok': r'"IDOK"\s*,\s*"([^"]*)"',
	# Used to retrieve the file from this for a bunch of situations:
	# >>> [Jrn.BasicFileInfo] Rvt.Attr.Worksharing: Not enabled Rvt.Attr.Username:  Rvt.Attr.CentralModelPath:  Rvt.Attr.RevitBuildVersion: Autodesk Revit 2022 ??? Rvt.Attr.LastSavePath: ??? Rvt.Attr.LTProject: notLTProject Rvt.Attr.LocaleWhenSaved: ENU Rvt.Attr.FileExt: rvt 
	'file_info': r'\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing:.*Rvt\.Attr\.LastSavePath: (.*?) Rvt\.Attr\.LTProject:',
	
	# Used to retrieve worksharing status for a bunch of file operations:
	# >>> # [Jrn.BasicFileInfo] Rvt.Attr.Worksharing: ??? Rvt.Attr.Username:  Rvt.Attr.CentralModelPath:  Rvt.Attr.RevitBuildVersion: Autodesk Revit 2022 ??? Rvt.Attr.LastSavePath: ??? Rvt.Attr.LTProject: notLTProject Rvt.Attr.LocaleWhenSaved: ENU Rvt.Attr.FileExt: rvt 
	'worksharing': r'\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.Username:.*Rvt\.Attr\.LTProject:',
	# Used to retrieve worksharing status while saving locally:
	# >>> [Jrn.ModelOperation] Rvt.Attr.Scenario: ModelSave COMMON.OS_VERSION: Microsoft Windows 10 Rvt.Attr.ModelVerEpisode: 6cc57073-dded-4210-8f2e-8e1cbefca187 34Rvt.Attr.ModelPath: RVT[8287748288871148745] Rvt.Attr.ModelSize: 0 Rvt.Attr.DetectDuration: 750 Rvt.Attr.Worksharing: WorkShared Rvt.Attr.ModelState: Normal 
	'modsave': r'\[Jrn\.ModelOperation\].*Rvt\.Attr\.Scenario: ModelSave.*Rvt.Attr.Worksharing: (.*?) Rvt\.Attr\.ModelState:',
	# Used to retrieve worksharing status while saving to the cloud:
	# >>> Jrn.AddInEvent "AddInJournaling"  , "WpfWindow(SaveAsCloudModelWindow,Save as Cloud Model).WpfSaveAsCloudModelBrowser(0,browser).Action(Save,b\.???,US,b\.???,__SHA,urn:adsk\.wipprod:fs\.folder:co\.???,???)" 
	'savecloud': r'Jrn\.AddInEvent.*WpfWindow(SaveAsCloudModelWindow,(.*?)).WpfSaveAsCloudModelBrowser',

	# Command process is interrupted by user pushing the ui button:
	# >>> 'H 29-Aug-2023 23:58:27.246;   0:< Jrn.Data  _ "File Name"  , "IDCANCEL" , "" 
	'cancel': r'IDCANCEL',
	# Request status is unknown (cloud cases):
	# >>> 0:< Autodesk.Bcg.Http.HttpRequestStatusException: Forbidden: Unknown response GetModelResponse 
	'request_unknown': r'HttpRequestStatusException.*Unknown response.*GetModelResponse.*',
	# Requestis failed, access is forbidden (cloud case):
	# >>> C 01-Sep-2023 18:07:12.846; 0:< HttpRequestFailedException "403" "Forbidden: Unknown response GetModelResponse" 
	'request_failed': r'HttpRequestFailedException.*403.*Forbidden.*',
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

				# get the ast entry if exists
				if self.data['ops']:
					cmd = self.data['ops'][-1]

					# cancellation & errors
					if (self._get_cmd_stop([schemes['cancel']], l) and not 'file' in cmd) or self._get_cmd_stop([schemes['request_unknown'], schemes['request_failed']], l):
						del self.data['ops'][-1]

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

					# we try to extract the data for started command from all suitable schemes:
					if cmd['cmd'] == 'open' and not 'file' in cmd:

							open_file = self._get_cmd_file([schemes['model_browser'], schemes['idok']], l)
							if open_file: cmd['file'] = open_file

					elif cmd['cmd'] == 'save' and not 'file' in cmd:

							save_file = self._get_cmd_file([schemes['onsave'], schemes['init'], schemes['idok']], l)
							if save_file: cmd['file'] = save_file

					elif cmd['cmd'] == 'sync' and not 'file' in cmd:

							sync_file = self._get_cmd_file([schemes['init'], schemes['file_info']], l)
							if sync_file: cmd['file'] = sync_file

					# cathing worksharing state
					if 'file' in cmd and not 'status' in cmd:
						status = self._get_cmd_status([schemes['worksharing'], schemes['modsave'], schemes['savecloud']], l)
						if status: cmd['status'] = status

				li += 1


		# just for case
		if self.data['ops'] and not 'file' in self.data['ops'][-1]:
			del self.data['ops'][-1]


	# extrat data from specific scheme parts
	@staticmethod
	def _get_cmd_stop(schemes, line):
		for s in schemes:
			q = re.search(s, line)
			if q:
				return True
				break

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