import sqlite3
import os
import time

from .system import System

class DB (System):

	def __init__(self):

		self.path = os.path.dirname(__file__).split('source')[0] + 'journals.db'
		self.connection = None
		self.cursor = None

		self.connect()
		self.tables()

	def connect(self):

		try:
			self.connection = sqlite3.connect(self.path)
			self.cursor = self.connection.cursor()

		except sqlite3.Error as e:
			print(f'SQLite error: {e}')


	def tables(self):

		try:
			self.cursor.execute('SELECT * FROM journals')

		except sqlite3.Error as e:
			print(f'SQLite error: {e}')
			self.c.execute(
				'CREATE TABLE IF NOT EXISTS journals \
				(id text primary key, mtime integer, name text, path text)'
			)


	def addJournalItem(self, uuid: str, mtime: int, name: str, path: str):

		self.cursor.execute("INSERT INTO journals (id, mtime, name, path) VALUES (?, ?, ?, ?)", (uuid, mtime, name, path))
		self.cursor.commit()


	def addCommandItem(self, uuid: str, idx: int, type: str, name: str, date: str, file: str, size: int, status: str):

		self.cursor.execute("INSERT INTO commands (id, idx, type, name, date, file, size, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (uuid, idx, type, name, date, file, size, status))
		self.cursor.commit()