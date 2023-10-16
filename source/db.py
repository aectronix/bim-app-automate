import sqlite3
import os

from .system import System

class DB (System):

	def __init__(self):

		self.name = 'journals.db'
		self.connection = None
		self.cursor = None
		self.logger = System().get_logger()
		self.config = System().get_config()

		self.connect()
		self.tables()

	def connect(self):

		self.logger.debug('Open connection with ' + self.config['colors']['y'] + self.name + self.config['colors']['x'] + '...')
		try:
			self.connection = sqlite3.connect(self.config['db']['path'] + self.name)
			self.cursor = self.connection.cursor()
			self.logger.info('Connection successful')

		except sqlite3.Error as e:
			self.logger.error(f'{e}')


	def tables(self):

		try:
			# self.cursor.execute('SELECT * FROM jobs')
			self.cursor.execute('SELECT * FROM journals')
			# self.cursor.execute('SELECT * FROM commands')
			self.logger.info('Tables found')

		except sqlite3.Error as e:
			self.logger.warning('No tables has been found, creating...')

			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS jobs \
				(id integer primary key, ts integer)'
			)
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS journals \
				(id text primary key, job integer, name text, mtime integer, build text, user text, path text)'
			)
			self.connection.execute(
				'CREATE TABLE IF NOT EXISTS commands \
				(id text primary key, jid text, job integer, idx integer, type text, name text, dt date, file text, size integer, status text)'
			)
			self.logger.info('Tables ' + self.config['colors']['y'] + 'jobs, journals, commands' + self.config['colors']['x'] + ' have been created')		


	def addJobItem(self, id, ts):

		self.cursor.execute("INSERT INTO jobs (id, ts) VALUES (?, ?)", (id, ts))
		self.connection.commit()


	def upsJournalItems(self, data):

		self.cursor.executemany("INSERT INTO journals (id, job, name, mtime, build, user, path) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (id) DO UPDATE SET mtime = excluded.mtime, job = excluded.job", data)
		self.connection.commit()


	def addCommandItems(self, data):

		self.cursor.executemany("INSERT INTO commands (id, jid, job, idx, type, name, dt, file, size, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", data)
		self.connection.commit()


	def getCommandItem(self, jid, idx, type, name, dt):

		query = self.cursor.execute('SELECT * FROM commands WHERE jid = ? AND idx = ? AND type = ? AND name = ? AND dt = ?', (jid, idx, type, name, dt))
		result = query.fetchone()

		return result