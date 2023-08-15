import os
import re

from datetime import datetime

class RevitJournal:

	__slots__ = ['name', 'path', 'build', 'data']

	def __init__(self, path):

		self.data = {
			'name':  os.path.basename(path),
			'path': path,
			'build': None,
			'user': None,
			'ops': {
				'open': []
			}
		}

		self.getJournalData()

	def getJournalData(self):

		with open(self.data['path'], 'r') as file:
			lines = file.readlines()

			li = 0
			for l in lines:

				# builds
				build = re.search(r"' Build:\s+(\S+)", l)
				if build:
					self.data['build'] = build.group(1)

				# user
				user = re.search(r'"Username"\s*,\s*"([^"]*)"', l)
				if user:
					self.data['user'] = user.group(1)

				# operations
				dt = None
				mode = 'local'

				# cloud
				open_cloud = re.search(r'Open Cloud Model Method: open.*Model Guid: ([a-fA-F0-9-]+)', l)
				if open_cloud:
					model_guid = re.search(r'"modelGuid"":""([a-fA-F0-9-]+)"', lines[li-1])
					if model_guid:
						model_name = re.search(r'"displayName"":""([^"]+)"', lines[li-1])
						if model_name:
							name = model_name.group(1)
							dt = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[li-2])
							if dt and name:
								# print(dt.group())
								self.data['ops']['open'].append({'date': dt.group(), 'file': name, 'mode': 'cloud'})

				# local & central
				open_ = re.search(r'Jrn.Command \"Ribbon\".*Open an existing project.*ID_REVIT_FILE_OPEN', l)
				if open_ and len(lines) > li+20:
					for i in range(li+1, li+20):
						check = re.search(r'"OpenAsLocalCheckBox"', lines[i])
						if check: mode = 'central'
						file_name = re.search(r'"File Name"\s*,\s*"IDOK"\s*,\s*"[^"]*\\([^\\"]+)"', lines[i])
						if file_name:
							# print(file_name.group(1))
							name = file_name.group(1)
							dt = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[li-1])
							if dt and name:
								self.data['ops']['open'].append({'date': dt.group(), 'file': name, 'mode': mode})

				li += 1