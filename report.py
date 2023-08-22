import argparse
import json
import time

import source

start_time = time.time()

cmd = argparse.ArgumentParser()
cmd.add_argument('-d', '--dest', required=True, help='Destination')
arg = cmd.parse_args()

cde = source.CDE(arg.dest)

for journal in cde.journals:
	# print('.')
	# print(journal.data['ops']['open'])
	if journal.data['ops']:
		print(json.dumps(journal.data, indent = 4))

# print(json.dumps(journals, indent = 4))

print("\n%s sec" % (time.time() - start_time))