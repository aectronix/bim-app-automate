import sqlite3
import os

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
			# self.cursor.execute('SELECT * FROM jobs')
			self.cursor.execute('SELECT * FROM journals')
			# self.cursor.execute('SELECT * FROM commands')

		except sqlite3.Error as e:
			print(f'SQLite error: {e}')
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS journals \
				(id text primary key, mtime integer, name text, path text)'
			)
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS commands \
				(id text primary key, jid text, idx int, type text, name text, dt date, file text, size int, status text, build text, user text)'
			)


	def addJournalItem(self, uuid: str, mtime: int, name: str, path: str):

		self.cursor.execute("INSERT INTO journals (id, mtime, name, path) VALUES (?, ?, ?, ?)", (uuid, mtime, name, path))
		self.connection.commit()


	def addCommandItem(self, id: str, jid: str, idx: int, type: str, name: str, dt: str, file: str, size: int, status: str, build: str, user: str):

		self.cursor.execute("INSERT INTO commands (id, jid, idx, type, name, dt, file, size, status, build, user) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (id, jid, idx, type, name, dt, file, size, status, build, user))
		self.connection.commit()