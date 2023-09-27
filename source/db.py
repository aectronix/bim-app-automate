import sqlite3
import os
import time
import uuid

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

		c = self.dbcon.cursor()

		try:
			c.execute('SELECT * FROM journals')

		except sqlite3.Error as e:
			print(f'SQLite error: {e}')
			c.execute(
				'CREATE TABLE IF NOT EXISTS journals \
				(id text primary key, name text, mtime real, build text, user text)'
			)

	def addJournalItem(self, name: str, mtime: float, build: str, user: str):

		c = self.dbcon.cursor()
		c.execute("INSERT INTO journals (id, name, mtime, build, user) VALUES (?, ?, ?, ?, ?)", (str(uuid.uuid4()), name, mtime, build, user))
		self.dbcon.commit()