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

				commands = j.getCommandData()
				for c in commands:
					if j and c:

						com = db.cursor.execute('SELECT * FROM commands WHERE jid = ? AND idx = ? AND type = ? AND name = ? AND dt = ?', (j.id, c.idx, c.type, c.name, c.dt)).fetchone()
						if not com:
							# db.addCommandItem(str(uuid.uuid4()), j.id, c.idx, c.type, c.name, c.dt, c.file, c.size, c.status, c.build, c.user)
							print(json.dumps({'id': j.id, 'journal': j.name, 'build': j.build, 'user': j.user, 'commands': { 'idx': c.idx, 'type': c.type, 'command': c.name, 'date': c.dt, 'file': c.file, 'size': c.size, 'status': c.status}}, ensure_ascii=False, indent = 4))
							cc += 1


	if journals: db.upsJournalItems(journals)


	print(cc)


runCollector()

print("%s sec" % (time.time() - start_time))