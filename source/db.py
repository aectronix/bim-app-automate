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
				(id text primary key, name text, mtime integer, build text, user text, path text)'
			)
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS commands \
				(id text primary key, jid text, idx int, type text, name text, dt date, file text, size int, status text)'
			)


	# def upsJournalItem(self, uuid: str, name: str, mtime: int, build: str, user: str, path: str):

	# 	self.cursor.execute("INSERT INTO journals (id, name, mtime, build, user, path) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET mtime = excluded.mtime", (uuid, name, mtime, build, user, path))
	# 	self.connection.commit()


	def upsJournalItems(self, data):

		self.cursor.executemany("INSERT INTO journals (id, name, mtime, build, user, path) VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET mtime = excluded.mtime", data)
		self.connection.commit()


	# def addCommandItem(self, id: str, jid: str, idx: int, type: str, name: str, dt: str, file: str, size: int, status: str):

	# 	self.cursor.execute("INSERT INTO commands (id, jid, idx, type, name, dt, file, size, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (id, jid, idx, type, name, dt, file, size, status))
	# 	self.connection.commit()

	def getCommandItem(self, jid, idx, type, name, dt):

		query = self.cursor.execute('SELECT * FROM commands WHERE jid = ? AND idx = ? AND type = ? AND name = ? AND dt = ?', (jid, idx, type, name, dt))
		result = query.fetchone()

		return result


	def addCommandItems(self, data):

		self.cursor.executemany("INSERT INTO commands (id, jid, idx, type, name, dt, file, size, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
		self.connection.commit()