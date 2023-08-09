import argparse
import json
import time

import source

start_time = time.time()

cmd = argparse.ArgumentParser()
cmd.add_argument('-d', '--dest', required=True, help='Destination')
arg = cmd.parse_args()

cde = source.CDE()
journals = cde.getJournalPaths(cde.getHostUsers(arg.dest))
for j in cde.getJournalData(journals):
	print(j.name + ' --> build: ' + j.build)

# print(json.dumps(journals, indent = 4))

print("\n%s sec" % (time.time() - start_time))