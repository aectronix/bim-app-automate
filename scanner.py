import argparse
import json
import math
import os
import time
import uuid

from source.cde import CDE
from source.db import DB
from source.revit import Revit
from source.revit import RevitJournal
from source.system import System

start_time = time.time()

cmd = argparse.ArgumentParser()
cmd.add_argument('-u', '--user', required=True, help='user login')
cmd.add_argument('-p', '--pwd', required=True, help='user password')
arg = cmd.parse_args()


def runCollector():

	sys = System()
	logger = sys.get_logger()
	logger.debug('Starting scanner app...')

	db = DB()
	cde = CDE(arg.user, arg.pwd)
	rvt = Revit()

	journals = list()
	commands = list()

	# log started job
	job = db.cursor.execute("SELECT * FROM jobs WHERE id = (SELECT MAX(id) FROM jobs)").fetchone()
	jobId = job[0]+1 if job else 0
	db.addJobItem(jobId, math.floor(time.time()))

	cde.logger.debug('Job ' + cde.config['colors']['y'] + '#' + str(jobId) + cde.config['colors']['x'] + ' started')

	hn = jn = cn = 0

	# for specified cde network
	cde.logger.debug('Retrieving network nodes...')
	for host in ['10.8.88.206', '10.8.89.97', '10.8.89.997']:
		hn += 1
		# retrieve journals, sync new or modified with database
		for journal in cde.getJournals(host):
			jn +=1
			attr = cde.connection.getAttributes('C$', journal)
			if attr:
				cde.logger.debug('Found ' + cde.config['colors']['y'] + attr.filename + cde.config['colors']['x'] + ', checking...')
				jid = None
				jpath = '\\\\' + host + '\\C$' + journal
				row = db.cursor.execute('SELECT * FROM journals WHERE name = ? AND path = ?', (attr.filename, jpath)).fetchone()

				# only new and modified
				if not row: jid = str(uuid.uuid4())
				elif row[3] < math.floor(attr.last_write_time): jid = row[0]

				if jid:
					text = cde.getFileText(journal)
					data = rvt.getJournalData(text)
					if data:
						j = RevitJournal(jid, attr.filename, math.floor(attr.last_write_time), jpath, data['build'], data['user'])
						cde.logger.info('Valid content found, parsing started...')
						journals.append((j.id, jobId, j.name, j.mtime, j.build, j.user, j.path)) # prep for db
						for c in rvt.getCommandData(j, text):
							cn += 1
							# only new
							if c and not db.getCommandItem(j.id, c.idx, c.type, c.name, c.dt):
								commands.append((str(uuid.uuid4()), j.id, jobId, c.idx, c.type, c.name, c.dt, c.file, c.size, c.status)) # prep for db
								# print(json.dumps({'journal': j.name, 'build': j.build, 'user': j.user, 'commands': {'type': c.type,'date': c.dt}}, ensure_ascii=False, indent = 4))



	# sync
	cde.logger.debug('Sync entries with database...')
	# if journals: db.upsJournalItems(journals)
	# if commands: db.addCommandItems(commands)

	cde.logger.info('Processed journals: ' + cde.config['colors']['y'] + str(len(journals)) + cde.config['colors']['x'] + '/' + str(jn) + ', commands: ' + cde.config['colors']['y'] + str(len(commands)) + cde.config['colors']['x'] + '/' + str(cn))
	cde.logger.debug(cde.config['colors']['y'] + str(round((time.time() - start_time), 3)) + 's')

runCollector()
