import os
import re

from datetime import datetime

from .system import System
# from source.db import DB

# The bunch of schemes to extract the primary command
commands = [
	# open from ribbon menu
	# > Jrn.RibbonEvent "ModelBrowserOpenDocumentEvent:open:{""projectGuid"":null,""modelGuid"":null,""id"":""C:\\Users\\user\\Desktop\\saving_test.rvt"",""displayName"":""saving_test"",""region"":null,""modelVersion"":""0""}"
	{ 'open': r'Jrn\.RibbonEvent.*(ModelBrowserOpenDocumentEvent:open)' },
	# app commands
	# > Jrn.Command "Ribbon"  , "Open an existing project , ID_REVIT_FILE_OPEN"
	{ 'open': r'Jrn\.Command.*,\s(ID_REVIT_FILE_OPEN|ID_APPMENU_PROJECT_OPEN|ID_FAMILY_OPEN|ID_IMPORT_IFC)"' },
	{ 'save': r'Jrn\.Command.*,\s(ID_REVIT_FILE_SAVE|ID_REVIT_FILE_SAVE_AS|ID_REVIT_SAVE_AS_TEMPLATE|ID_SAVE_FAMILY|ID_REVIT_SAVE_AS_FAMILY)"' },
	{ 'sync': r'Jrn\.Command.*,\s(ID_FILE_SAVE_TO_CENTRAL|ID_FILE_SAVE_TO_MASTER_SHORTCUT|ID_COLLABORATE)"' },
	{ 'exit': r'Jrn\.Command.*,\s(ID_REVIT_FILE_CLOSE|ID_APP_EXIT)"' },
]

# The bunch of schemes to extract the command data
schemes = {

	# Check uuid
	# > 8c780472-dc98-48b8-869e-4255d43e8e97
	'uuid': r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',

	# Separate file from path
	# > {path}
	'file': r'[\\/](?=[^\\/]*$)(.+)$',

	# Get file path and file size
	# > Detect if missing elements for {path}: File Size: {size}, Element Count: 22691 
	'detect': { 'pattern': r'Detect if missing elements for (.*?): File Size: (-?\d+), Element Count: \d+', 'items': ['file', 'size'] },
	
	# Get file name
	# > "IDOK", "{path}"
	'idok': { 'pattern': r'"IDOK"\s*,\s*"([^"]*)"', 'items': ['file'] },

	# Get file size
	# > Jrn.Directive "FileSizeComparison" , "20230912153851", "2021(20210426_1515(x64))", {size}
	'fsizecomp': { 'pattern': r'FileSizeComparison.*\)".*\b(\d+)\b', 'items': ['size'] },
	
	# Get file size
	# > skybase_model_size_bytes: {size}
	'skybase': { 'pattern': r'skybase_model_size_bytes:.*\b(\d+)\b', 'items': ['size'] },

	# Get worksharing status and file path
	# > [Jrn.BasicFileInfo] Rvt.Attr.Worksharing: {status} Rvt.Attr.Username:  Rvt.Attr.CentralModelPath: {path1} Rvt.Attr.RevitBuildVersion: Autodesk Revit 2021 (Build: 20210426_1515(x64)) Rvt.Attr.LastSavePath: {path2} Rvt.Attr.LTProject: notLTProject Rvt.Attr.LocaleWhenSaved: ENU Rvt.Attr.FileExt: rvt'
	'finfo': { 'pattern': r'\[Jrn\.BasicFileInfo\].*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.Username:.*Rvt\.Attr\.CentralModelPath: (.*?) Rvt.Attr.RevitBuildVersion:.*Rvt\.Attr\.LastSavePath:(.*?) Rvt\.Attr\.LTProject:', 'items': ['status', 'file', 'file'] },

	# Get file size
	# > C 12-Sep-2023 14:20:34.548;  fileSizeOnOpen:{size}KB
	'fsizeopen': { 'pattern': r'fileSizeOnOpen:(\d+)KB', 'items': ['size'] },

	# get worksharing status and file name
	# > 5:< SLOG $576608a2 2023-09-11 18:51:56.272 >{status}  "{path}"
	'saveas': { 'pattern': r'SLOG .* >(\w+)  "(.*?)"', 'items': ['status', 'file'] },

	# Get worksharing status
	# > [Jrn.ModelOperation] Rvt.Attr.Scenario: ModelSave COMMON.OS_VERSION: Microsoft Windows 10 Rvt.Attr.ModelVerEpisode: ... 3Rvt.Attr.ModelPath: RVT[...] Rvt.Attr.ModelSize: 0 Rvt.Attr.DetectDuration: 16 Rvt.Attr.Worksharing: {status}  Rvt.Attr.ModelState: Normal
	'modelsave': { 'pattern': r'Jrn\.ModelOperation.*Rvt\.Attr\.Scenario.*ModelSave.*Rvt\.Attr\.Worksharing: (.*?) Rvt\.Attr\.ModelState:', 'items': ['status'] },

	# Get command type
	# > Jrn.Data "TaskDialogResult"  _ , "You have made changes to model test-srv-2_user.rvt that have not been saved.  What do you want to do?",  _ "Synchronize with central", "{code}"
	'tsync': { 'pattern': r'You have made changes to model.*"1001"', 'items': ['type'] , 'match': 'sync' },
	'tsave': { 'pattern': r'You have made changes to model.*"1002"', 'items': ['type'] , 'match': 'save' },
	# > Jrn.Data  _ "TaskDialogResult" , "Do you want to save changes to collaborateTest.rvt?" ,  _ "Yes"  _ , "IDYES" 
	# > Jrn.Data  _ "TaskDialogResult" , "This is the first time that the project has been saved since Worksharing was enabled. This project will therefore become the central model. Do you want to save this project as the central model?" ,  _ "Yes"  _ , "IDYES" 
	'saveyes': { 'pattern': r'Do you want to save.*"IDYES"', 'items': ['type'] , 'match': 'save' },

	# Detect cancellation or errors
	# > Jrn.Data  _ "File Name"  , "IDCANCEL" , "" 
	'idcancel': { 'pattern': r'IDCANCEL', 'items': ['stop'] , 'match': True },
	# > Jrn.AddInEvent "AddInJournaling"  , "WpfWindow(Collaborate,Collaborate).WpfButton(0,CancelButton).Click()"
	'btcancel': { 'pattern': r'AddInJournaling.*WpfButton\(0,CancelButton\)\.Click', 'items': ['stop'] , 'match': True },
	# > 0:< Autodesk.Bcg.Http.HttpRequestStatusException: Forbidden: Unknown response GetModelResponse
	'error': { 'pattern': r'HttpRequestStatusException.*Unknown response.*GetModelResponse.*', 'items': ['stop'] , 'match': True },
	# > C 01-Sep-2023 18:07:52.112; 0:< HttpRequestFailedException "403" "Forbidden: Unknown response GetModelResponse"
	'error403': { 'pattern': r'HttpRequestFailedException.*403.*Forbidden.*', 'items': ['stop'] , 'match': True },

}


class RevitJournal:

	__slots__ = ['uuid', 'name', 'path', 'mtime', 'build', 'user', 'commands', 'db']

	def __init__(self, uuid: str, path: str):

		self.uuid = uuid
		self.path = path
		self.name = os.path.basename(path)
		self.mtime = os.path.getmtime(path)
		self.build = None
		self.user = None
		self.commands = list()

		self.getCommandData()


	def getCommandData(self):

		with open(self.path, 'r') as file:

			lines = file.readlines()
			li = 0

			for l in lines[:-1]:

				# builds
				build = re.search(r"' Build:\s+(\S+)", l)
				if build:
					self.build = build.group(1)

				# users
				user = re.search(r'"Username"\s*,\s*"([^"]*)"', l)
				if user:
					self.user = user.group(1)

				# try to catch the commands
				for c in commands:
					command = re.search(c[next(iter(c))], l)
					if command:
						if self.commands and isinstance(self.commands[-1], RevitCommand) and not self.commands[-1].file:
							del self.commands[-1]
						date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[li-1])
						self.commands.append(RevitCommand(li+1, next(iter(c)), command.group(1), date.group(0)))
						break

				# get the ast entry if exists
				if self.commands and isinstance(self.commands[-1], RevitCommand):
					cmd = self.commands[-1]

					# cancellation & errors
					if (self._parse_by_scheme([schemes['idcancel']], l) and not cmd.file) or self._parse_by_scheme([schemes['btcancel'], schemes['error'], schemes['error403']], l):
						del self.commands[-1]

					# transform exit commands into the final ones
					if cmd.type == 'exit':
						task = self._parse_by_scheme([schemes['tsync'], schemes['tsave'], schemes['saveyes']], re.sub(r'\s+', ' ', l + lines[li+1] + lines[li+2]))
						if not task: del self.commands[-1]
						else: cmd.type = task['type']

					# try parsing schemes to retrieve the data
					if not cmd.file:
						fname = self._parse_by_scheme([schemes['idok'], schemes['detect'], schemes['finfo']], l)
						for d in fname:
							if not getattr(cmd, d): setattr(cmd, d, fname[d])

					if not cmd.size:
						size = self._parse_by_scheme([schemes['fsizecomp'], schemes['fsizeopen'], schemes['skybase'], schemes['detect']], re.sub(r'\s+', ' ', l + lines[li+1]))
						for d in size:
							if not getattr(cmd, d): setattr(cmd, d, size[d])

					if not cmd.status:
						status = self._parse_by_scheme([schemes['finfo'], schemes['saveas'], schemes['modelsave']], l)
						for d in status:
							if not getattr(cmd, d): setattr(cmd, d, status[d])

				li += 1


	@staticmethod
	def _parse_by_scheme(schemlist, line, ):
		result = {}
		for s in schemlist:
			q = re.search(s['pattern'], line)
			if q:
				if not 'match' in s:
					for i in range(len(s['items'])):
						# distinguish name from path 
						if s['items'][i] == 'file':
							result['filepath'] = q.group(i+1)
							file = re.search(schemes['file'], q.group(i+1))
							if file and not re.match(schemes['uuid'], file.group(1)):
								result['file'] = file.group(1)
							else:
								pass
						else:
							result[s['items'][i]] = q.group(i+1)
				elif 'match' in s:

					result[s['items'][0]] = s['match']
				break
		return result


class RevitCommand:

	def __init__(self, idx: int, type: str, name: str, date: str):

		self.idx = idx
		self.type = type
		self.name = name
		self.date = date
		self.file = None
		self.filepath = None
		self.size = None
		self.status = None