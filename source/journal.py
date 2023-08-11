import os
import re

class RevitJournal:

	__slots__ = ['name', 'path', 'build']

	def __init__(self, path):

		self.name = os.path.basename(path)
		self.path = path
		self.build = None

		self.getFileData()

	def getFileData(self):

		with open(self.path, 'r') as data:
		    for r in data:
		        match = re.search(r' Build: ', r)
		        if match:
		        	self.build = r[match.end():].strip()