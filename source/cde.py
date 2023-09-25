import os
from .journal import RevitJournal

USER_DIRECTORY = '\\C$\\Users'
JOURNAL_DIRECTORY = '\\AppData\\Local\\Autodesk\\Revit'
JOURNALS_FOLDER_NAME = 'Journals'
FILTERS = {'user': ['All Users', 'archadm', 'Default', 'Default User', 'Public', 'Администратор', 'Все пользователи']}

class CDE:
	def __init__(self, host):
		self.host = host
		self.user_directories = None
		self.journal_pathes = None
		self.journals = None

		self.get_host_user_directories()
		self.get_journal_pathes()
		self.get_journal_data()


	def get_host_user_directories(self):
		"""Returns filtered list of the host directories for each user 
		"""
		host_user_directory = self.host + USER_DIRECTORY
		user_directories = [os.path.join(host_user_directory, directory) for directory in os.listdir(host_user_directory) 
																			if not directory in FILTERS['user']]
		user_directories = [directory for directory in user_directories if os.path.isdir(directory)]

		self.user_directories = user_directories
		#return user_directories


	def get_journal_pathes(self):
		"""Returns list of all journal text file pathes
		"""
		journal_pathes = list()
		for user_directory in self.user_directories:
			path = user_directory + JOURNAL_DIRECTORY

			if os.path.isdir(path):
				revit_versions = [os.path.join(path, directory) for directory in os.listdir(path) if 'Autodesk Revit 20' in directory]
				for revit_version in revit_versions:
					journal_path = os.path.join(revit_version, JOURNALS_FOLDER_NAME)

					if os.path.isdir(journal_path):
						current_journals = [current for current in os.listdir(journal_path) if '.txt' in current]
						current_journals = [current for current in current_journals if '.abbrev' not in current]
						current_journals_pathes = [os.path.join(journal_path, current) for current in current_journals]
						journal_pathes += current_journals_pathes
					else: print("No Autodesk Revit journal folder found:(")

			else: print("No Autodesk Revit folder found:(")

		if not journal_pathes: print("No Autodesk Revit journals found:(")

		self.journal_pathes = journal_pathes
		#return journal_pathes

		# TODO: filter journal by modifitaction timestamp


	def get_journal_data(self):
		"""Creates Journal from all text files and returns list of them
		"""
		journals = [RevitJournal(current) for current in self.journal_pathes]
		self.journals = journals
		#return journals
