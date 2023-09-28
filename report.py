import argparse
import json
import time

import source
from source.db import DB

start_time = time.time()

cmd = argparse.ArgumentParser()
cmd.add_argument('-d', '--dest', required=True, help='Destination')
arg = cmd.parse_args()

cde = source.CDE(arg.dest, DB())
journals = cde.getJournalsData(cde.getJournals())

comNum = 0
# for journal in cde.getJournalData():
# 	# print('.')
# 	# print(journal.data['ops']['open'])
# 	if journal.data['ops']:
# 		comNum = comNum + len(journal.data['ops'])
# 		print(json.dumps(journal.data, ensure_ascii=False, indent = 4))
for j in journals:
	# print('.')
	# print(journal.data['ops']['open'])
	if j:
		# print(j.name)
		for c in j.commands:
			# print([c.name, c.file, c.size, c.status])
			print(json.dumps({'id': j.uuid, 'journal': j.name, 'build': j.build, 'commands': { 'idx': c.idx, 'type': c.type, 'command': c.name, 'date': c.date, 'file': c.file, 'size': c.size, 'status': c.status}}, ensure_ascii=False, indent = 4))
			comNum += 1
		# print(json.dumps(j.data, ensure_ascii=False, indent = 4))


print('\n' + str(comNum))

# print(json.dumps(journals, indent = 4))

print("%s sec" % (time.time() - start_time))