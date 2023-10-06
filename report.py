import argparse
import json
import math
import os
import time
import uuid

from smb.SMBConnection import SMBConnection

from source.cde import CDE
from source.db import DB
from source.journal import RevitJournal

start_time = time.time()

cmd = argparse.ArgumentParser()
cmd.add_argument('-d', '--dest', required=True, help='Destination')
arg = cmd.parse_args()


def runCollector():

	db = DB()
	cde = CDE(arg.dest)

	journals = list()
	commands = list()

	cc = 0

	# retrieve journals, sync new or modified with database
	for jpath in cde.getJournals():

		mtime = math.floor(os.path.getmtime(jpath))
		row = db.cursor.execute('SELECT * FROM journals WHERE name = ? AND path = ?', (os.path.basename(jpath), jpath)).fetchone()
		jid = None

		# only new and modified
		if not row: jid = str(uuid.uuid4())
		elif row[2] < mtime: jid = row[0]

		if jid:
			j = RevitJournal(jid, jpath)
			if j.build and j.user:
				journals.append((j.id, j.name, j.mtime, j.build, j.user, j.path))

				# only new
				for c in j.getCommandData():
					if c and not db.getCommandItem(j.id, c.idx, c.type, c.name, c.dt):
						commands.append((str(uuid.uuid4()), j.id, c.idx, c.type, c.name, c.dt, c.file, c.size, c.status))
						cc += 1


	# sync with db
	if journals: db.upsJournalItems(journals)
	if commands: db.addCommandItems(commands)

	print(cc)


runCollector()
print("%s sec" % (time.time() - start_time))