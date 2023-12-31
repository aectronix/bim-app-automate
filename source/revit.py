import math
import os
import re
import uuid

from .system import System

class Revit (System):

	def __init__(self):

		self.config = System().get_config()
		self.logger = System().get_logger()

	def getJournalData(self, data):

		build = None
		user = None
		schemes = self.config['journal']['patterns']['contents']

		li = 0
		lines = data.splitlines()
		d = len(lines) if len(lines) < 150 else 150

		for l in lines[0:d-1]:

			b = re.search(r'' + schemes['build'], l)
			if b:
				if b.group(1) in self.config['journal']['versions']:
					build = self.config['journal']['versions'][b.group(1)]
				else:
					build = b.group(1)

			u = re.search(r'' + schemes['user'], re.sub(r'\s+', ' ', l + lines[li+1]))
			if u: user = u.group(1)

			li += 1

			if build and user:
				return { 'build': build, 'user': user }

	def getCommandData(self, journal, data):	

		schemes = self.config['journal']['patterns']['contents']
		msg = self.config['logger']['messages']
		commands = list()

		li = 0
		lines = data.splitlines()

		for l in lines[:-2]:

			# try to catch the commands
			for ac in self.config['journal']['patterns']['commands']:
				appcom = re.search(ac[next(iter(ac))], l)
				if appcom:
					self.logger.debug(msg['jrn_command_found'].format(appcom.group(1), str(li+1)))
					if commands and isinstance(commands[-1], RevitCommand) and not commands[-1].file:
						self.logger.warning(msg['jrn_command_empty'])
						del commands[-1]
					date = re.search(r'\d{2}-[A-Za-z]{3}-\d{4} \d{2}:\d{2}:\d{2}', lines[li-1])
					commands.append(RevitCommand(journal.id, li+1, next(iter(ac)), appcom.group(1), date.group(0)))
					break

			# get the ast entry if exists
			if commands and isinstance(commands[-1], RevitCommand):
				cmd = commands[-1]

				# cancellation & errors
				if (self.getParsedPattern([schemes['idcancel']], l) and not cmd.file) or self.getParsedPattern([schemes['btcancel'], schemes['error'], schemes['error403']], l) or self.getParsedPattern([schemes['version'], schemes['detach']], re.sub(r'\s+', ' ', l + lines[li+1] + lines[li+2])):
					self.logger.warning(msg['jrn_command_break'])
					del commands[-1]

				# transform exit commands into the final ones
				if cmd.type == 'exit':
					task = self.getParsedPattern([schemes['tsync'], schemes['tsave'], schemes['saveyes']], re.sub(r'\s+', ' ', l + lines[li+1] + lines[li+2]))
					if task:
						cmd.type = task['type']
						self.logger.debug(msg['jrn_command_exit'].format(cmd.type))
					elif self.getParsedPattern([schemes['savenot']], re.sub(r'\s+', ' ', l + lines[li+1] + lines[li+2])):
						del commands[-1]

				# try parsing schemes to retrieve the data
				if not cmd.file:
					fname = self.getParsedPattern([schemes['idok'], schemes['elements'], schemes['finfo']], l)
					if fname:
						for d in fname:
							self.logger.debug(msg['jrn_command_prop'].format(d, fname[d], li+1))
							if not getattr(cmd, d): setattr(cmd, d, fname[d])

				if not cmd.size:
					size = self.getParsedPattern([schemes['fsizecomp'], schemes['fsizeopen'], schemes['skybase'], schemes['elements']], re.sub(r'\s+', ' ', l + lines[li+1]))
					for d in size:
						self.logger.debug(msg['jrn_command_prop'].format(d, size[d], li+1))
						if not getattr(cmd, d): setattr(cmd, d, size[d])

				if not cmd.status:
					status = self.getParsedPattern([schemes['finfo'], schemes['saveas'], schemes['operation'], schemes['onsave'], schemes['upload']], l)
					for d in status:
						self.logger.debug(msg['jrn_command_prop'].format(d, status[d], li+1))
						if not getattr(cmd, d): setattr(cmd, d, status[d])	

			li += 1

		# we don't need commands with empty object
		if commands and not commands[-1].file:
			self.logger.warning(msg['jrn_command_empty'])
			del commands[-1]

		return commands

	def getParsedPattern(self, schemlist, line):

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


class RevitJournal:

	def __init__(self, id, name, mtime, path, size=0, build=None, user=None):

		self.id = id
		self.name = name
		self.mtime = mtime
		self.path = path
		self.size = size
		self.build = build
		self.user = user


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