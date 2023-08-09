import os
from .journal import RevitJournal

class CDE:

	def __init__(self):
		self.filters = {}
		self.filters['user'] = ['All Users', 'archadm', 'Default', 'Default User', 'Public', 'Администратор', 'Все пользователи']


	def getHostUsers(self, host):

		userPaths = []
		path = host+'\\C$\\Users'
		for i in os.listdir(path):
			if os.path.isdir(os.path.join(path, i)) and not i in self.filters['user']:
				userPaths.append(os.path.join(path, i))
				return userPaths

	def getJournalPaths(self, users):

		journals = []
		for u in users:
			path = u+'\\AppData\\Local\\Autodesk\\Revit'
			try:
				for i in os.listdir(path):
					if 'Autodesk Revit 20' in i:
						try:
							path_j = os.path.join(path, i+'\\Journals')
							for j in os.listdir(path_j):
								if '.txt' in j and not '.abbrev' in j:
									journals.append(os.path.join(path_j, j))
									
						except Exception as e:
							print('no autodesk revit folders found')
				return journals

			except Exception as e:
				print('no autodesk revit folders found')

	def getJournalData(self, journals):

		result = []
		for j in journals:
			result.append(RevitJournal(os.path.basename(j), j))

		return result
