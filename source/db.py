import sqlite3
import os
import time

class DB:

	def __init__(self):

		self.dbpath = os.path.dirname(__file__).split('source')[0] + 'journals.db'
		self.dbcon = None

		self.connect()
		self.tables()

	def connect(self):

		try:
			connect = sqlite3.connect(self.dbpath)
			self.dbcon = connect

		except sqlite3.Error as e:
			print(f'SQLite error: {e}')


	def tables(self):

		try:
			c = self.dbcon.cursor()
			c.execute('SELECT * FROM journals')

		except sqlite3.Error as e:
			print(f'SQLite error: {e}')
			c.execute(
				'CREATE TABLE IF NOT EXISTS journals \
				(id text primary key, mtime integer, name text, path text)'
			)


	def addJournalItem(self, uuid: str, mtime: int, name: str, path: str):

		c = self.dbcon.cursor()
		c.execute("INSERT INTO journals (id, mtime, name, path) VALUES (?, ?, ?, ?)", (uuid, mtime, name, path))
		self.dbcon.commit()