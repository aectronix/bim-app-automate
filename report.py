import argparse
import json
import math
import os
import time
import uuid

from smb.SMBConnection import SMBConnection

from source.cde import CDE
from source.db import DB


start_time = time.time()

cmd = argparse.ArgumentParser()
cmd.add_argument('-d', '--dest', required=True, help='Destination')
arg = cmd.parse_args()

def runCollector():

	db = DB()
	cde = CDE(arg.dest)
	journals = cde.getJournals()
	filtered = list()

	cc = 0

	# retrieve journals, sync new or modified with database
	for jpath in journals:
		mtime = math.floor(os.path.getmtime(jpath))
		jrn = db.cursor.execute('SELECT * FROM journals WHERE name = ? AND path = ?', (os.path.basename(jpath), jpath)).fetchone()						

		if not jrn:
			jid = str(uuid.uuid4())
			filtered.append({'id': jid, 'path': jpath})
			db.addJournalItem(jid, mtime, os.path.basename(jpath), jpath)
		elif jrn[1] < mtime:
			filtered.append({'id': jrn[0], 'path': jpath})
			db.cursor.execute('UPDATE journals SET mtime = ? WHERE id = ?', (mtime, jrn[0]))
			db.connection.commit()

	# get journal & command data, save new commands
	for j in cde.getJournalsData(filtered):
		for c in j.commands:
			# if j:
			# 	print(j.name)
			if j and c:

				com = db.cursor.execute('SELECT * FROM commands WHERE jid = ? AND idx = ? AND type = ? AND name = ? AND dt = ? AND build = ?', (j.id, c.idx, c.type, c.name, c.dt, c.build)).fetchone()
				if not com:
					db.addCommandItem(str(uuid.uuid4()), j.id, c.idx, c.type, c.name, c.dt, c.file, c.size, c.status, c.build, c.user)
					print(json.dumps({'id': j.id, 'journal': j.name, 'build': j.build, 'user': j.user, 'commands': { 'idx': c.idx, 'type': c.type, 'command': c.name, 'date': c.dt, 'file': c.file, 'size': c.size, 'status': c.status}}, ensure_ascii=False, indent = 4))
					cc += 1

	print(cc)

runCollector()


print("%s sec" % (time.time() - start_time))