import math
import os
import re
import uuid

from .system import System

class RevitJournal (System):

	def __init__(self, id, path: str):

		self.id = id
		self.path = path
		self.name = os.path.basename(path)
		self.mtime = math.floor(os.path.getmtime(path))
		self.build = None
		self.user = None

		self.getBasicData()

	def getBasicData(self):

		schemes = self.config['journal']['patterns']['contents']
		with open(self.path, 'r') as file:

			li = 0
			lines = file.readlines()
			d = len(lines) if len(lines) < 150 else 150

			for l in lines[0:d-1]:

				build = re.search(r'' + schemes['build'], l)
				if build:
					if build.group(1) in self.config['journal']['versions']:
						self.build = self.config['journal']['versions'][build.group(1)]
					else:
						self.build = build.group(1)

				user = re.search(r'' + schemes['user'], re.sub(r'\s+', ' ', l + lines[li+1]))
				if user: self.user = user.group(1)

				if self.build and self.user: break

				li += 1


	def getCommandData(self):

		schemes = self.config['journal']['patterns']['contents']
		commands = list()

		with open(self.path, 'r') as file:

			li = 0
			lines = file.readlines()

			for l in lines[:-2]:

				# try to catch the commands
				for ac in self.config['journal']['patterns']['commands']:
					appcom = re.search(ac[next(iter(ac))], l)
					if appcom:
						if commands and isinstance(commands[-1], RevitCommand) and not commands[-1].file:
							del commands[-1]
						date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[li-1])
						commands.append(RevitCommand(self.id, li+1, next(iter(ac)), appcom.group(1), date.group(0)))
						break

				# get the ast entry if exists
				if commands and isinstance(commands[-1], RevitCommand):
					cmd = commands[-1]

					# cancellation & errors
					if (self.parse_by_pattern([schemes['idcancel']], l) and not cmd.file) or self.parse_by_pattern([schemes['btcancel'], schemes['error'], schemes['error403']], l):
						del commands[-1]

					# transform exit commands into the final ones
					if cmd.type == 'exit':
						task = self.parse_by_pattern([schemes['tsync'], schemes['tsave'], schemes['saveyes']], re.sub(r'\s+', ' ', l + lines[li+1] + lines[li+2]))
						if task: cmd.type = task['type']
						elif self.parse_by_pattern([schemes['savenot']], re.sub(r'\s+', ' ', l + lines[li+1] + lines[li+2])):
							del commands[-1]

					# try parsing schemes to retrieve the data
					if not cmd.file:
						fname = self.parse_by_pattern([schemes['idok'], schemes['detect'], schemes['finfo']], l)
						for d in fname:
							if not getattr(cmd, d): setattr(cmd, d, fname[d])

					if not cmd.size:
						size = self.parse_by_pattern([schemes['fsizecomp'], schemes['fsizeopen'], schemes['skybase'], schemes['detect']], re.sub(r'\s+', ' ', l + lines[li+1]))
						for d in size:
							if not getattr(cmd, d): setattr(cmd, d, size[d])

					if not cmd.status:
						status = self.parse_by_pattern([schemes['finfo'], schemes['saveas'], schemes['modelsave']], l)
						for d in status:
							if not getattr(cmd, d): setattr(cmd, d, status[d])	

				li += 1

			# we don't need commands with empty object
			if commands and commands[-1].type == 'exit':
				del commands[-1]

		return commands


	def parse_by_pattern(self, schemlist, line):

		schemes = self.config['journal']['patterns']['contents']
		result = {}

		for s in schemlist:
			q = re.search(s['key'], line)
			if q:
				if not 'match' in s:
					for i in range(len(s['items'])):
						# distinguish name from path 
						if s['items'][i] == 'file':
							result['filepath'] = q.group(i+1)
							file = re.search(r'' + schemes['file'], q.group(i+1))
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

	def __init__(self, jid, idx, type, name, dt):

		self.id = str(uuid.uuid4())
		self.jid = jid
		self.idx = idx
		self.type = type
		self.name = name
		self.dt = dt
		self.file = None
		self.filepath = None
		self.size = None
		self.status = None