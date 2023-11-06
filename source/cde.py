import os
import re
import tempfile

from smb.SMBConnection import SMBConnection

from .system import System

class CDE (System):

	def __init__(self, user, password):

		self.user = user
		self.pwd = password
		self.host = '10.8.88.206'
		self.auth = False
		self.connection = None

		config = System().get_config()
		self.config = config
		self.logger = System().get_logger()
		self.msg = self.config['logger']['messages']

		self._authorize()


	def _authorize(self):

		self.logger.debug(self.msg['cde_auth'])
		try:
			connection = SMBConnection(self.user, self.pwd, '', self.config['cde']['network']['pysmb']['test'], use_ntlm_v2=True, is_direct_tcp=True)		
			if connection.connect(self.config['cde']['network']['pysmb']['test'], 445, timeout=15):
				data = connection.listPath('public', '\\')
				if data:
					self.auth = True
					self.logger.info(self.msg['cde_auth_ok'])

		except Exception as e:
			self.logger.error(f'{e}, authorization failed')

		connection.close()


	def getHosts(self):

		hosts = list()
		net = self.config['cde']['network']['nodes']

		if not self.host:
			hosts = [self.host,]
		else:
			for n in net:
				# get ranges and mask
				ip = net[n][0].split('.')
				start = net[n][0].split('.')[3]
				end = net[n][1].split('.')[3]
				for i in range(int(start), int(end)+1):
					hosts.append('.'.join(ip[:3]) + '.' + str(i))
		
		return hosts


	def getJournals(self, host):

		journals = list()

		self.logger.debug(self.msg['cde_net_host'].format(host))
		try:
			self.connection = SMBConnection(self.user, self.pwd, '', host, use_ntlm_v2=True, is_direct_tcp=True)
			self.connection.connect(host, 445, timeout=self.config['cde']['network']['pysmb']['timeout'])
			self.logger.info(self.msg['cde_net_host_ok'])

		except Exception as e:
			self.connection = None
			self.logger.error(f'{e}, ' + self.msg['cde_net_host_fail'].format(host))

		if self.connection:
			try:
				upath = '\\Users\\'
				usr_dir = self.connection.listPath('C$', upath)
				for u in usr_dir:
					if u.isDirectory and not u.filename in self.config['cde']['filters']['users']:
						rpath = upath + u.filename + '\\AppData\\Local\\Autodesk\\Revit\\'
						rvt_dir = self.connection.listPath('C$', rpath)
						for r in rvt_dir:
							if 'Autodesk Revit 20' in r.filename:
								jpath = rpath + r.filename + '\\Journals\\'
								jrn_dir = self.connection.listPath('C$', jpath)
								for j in jrn_dir:
									if re.match(r'journal.*\.txt$', j.filename):
										journals.append(jpath + j.filename)
			except Exception as e:
				self.logger.error(f'{e}')

			if not journals:
				self.logger.warning(self.msg['cde_no_seek'].format('journals'))

				self.connection.close()
				self.connection = None

		return journals


	def getFileText(self, path):

		data = None

		try:
			with tempfile.NamedTemporaryFile() as file:
				self.connection.retrieveFile('C$', path, file)
				file.seek(0)
				data = file.read().decode('latin-1')

			file.close()

		except Exception as e:
			self.logger.error(f'{e}')

		return data


