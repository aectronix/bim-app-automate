import sqlite3
import os

from .system import System
from .revit import Revit

class DB (System):

	def __init__(self):

		self.name = 'journals.db'
		self.connection = None
		self.cursor = None

		self.config = System().get_config()
		self.logger = System().get_logger()
		self.msg = self.config['logger']['messages']

		self.connect()
		self.tables()

	def connect(self):

		self.logger.debug(self.msg['db_connect'].format(self.name))
		try:
			self.connection = sqlite3.connect(self.config['db']['path'] + self.name)
			self.cursor = self.connection.cursor()
			self.logger.info(self.msg['db_connect_ok'])

		except sqlite3.Error as e:
			self.logger.error(f'{e}')


	def tables(self):

		try:
			# self.cursor.execute('SELECT * FROM jobs')
			self.cursor.execute('SELECT * FROM journals')
			# self.cursor.execute('SELECT * FROM commands')
			self.logger.info(self.msg['db_tables_ok'])

		except sqlite3.Error as e:
			self.logger.warning(self.msg['db_tables_none'])

			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS jobs \
				(id integer primary key, ts integer)'
			)
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS journals \
				(id text primary key, job integer, name text, mtime integer, size integer, build text, user text, path text)'
			)
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS commands \
				(id text primary key, jid text, job integer, idx integer, type text, name text, dt text, file text, size integer, status text)'
			)
			self.logger.info(self.msg['db_tables_made'].format('jobs, journals, commands'))	


	def addJobItem(self, id, ts):

		self.cursor.execute("INSERT INTO jobs (id, ts) VALUES (?, ?)", (id, ts))
		self.connection.commit()


	def upsJournalItems(self, data):

		self.cursor.executemany("INSERT INTO journals (id, job, name, mtime, size, build, user, path) VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET mtime = excluded.mtime, size = excluded.size, job = excluded.job", data)
		self.connection.commit()


	def addCommandItems(self, data):

		self.cursor.executemany("INSERT INTO commands (id, jid, job, idx, type, name, dt, file, size, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
		self.connection.commit()


	def getCommandItem(self, jid, idx, type, name, dt):

		query = self.cursor.execute('SELECT * FROM commands WHERE jid = ? AND idx = ? AND type = ? AND name = ? AND dt = ?', (jid, idx, type, name, dt))
		result = query.fetchone()

		return result