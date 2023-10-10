import sqlite3
import os

from .system import System

class DB (System):

	def __init__(self):

		self.connection = None
		self.cursor = None

		self.connect()
		self.tables()

	def connect(self):

		try:
			self.connection = sqlite3.connect(self.config['db']['path'])
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
				'CREATE TABLE IF NOT EXISTS jobs \
				(id integer primary key, ts integer)'
			)			
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS journals \
				(id text primary key, jbid integer, name text, mtime integer, build text, user text, path text)'
			)
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS commands \
				(id text primary key, jid text, jbid integer, idx integer, type text, name text, dt date, file text, size integer, status text)'
			)


	def addJobItem(self, id, ts):

		self.cursor.execute("INSERT INTO jobs (id, ts) VALUES (?, ?)", (id, ts))
		self.connection.commit()


	def upsJournalItems(self, data):

		self.cursor.executemany("INSERT INTO journals (id, jbid, name, mtime, build, user, path) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET mtime = excluded.mtime, jbid = excluded.jbid", data)
		self.connection.commit()


	def addCommandItems(self, data):

		self.cursor.executemany("INSERT INTO commands (id, jid, jbid, idx, type, name, dt, file, size, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
		self.connection.commit()


	def getCommandItem(self, jid, idx, type, name, dt):

		query = self.cursor.execute('SELECT * FROM commands WHERE jid = ? AND idx = ? AND type = ? AND name = ? AND dt = ?', (jid, idx, type, name, dt))
		result = query.fetchone()

		return result