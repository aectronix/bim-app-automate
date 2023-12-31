import colorama
import json
import logging
import os
import time

class System:

	_instances = {}
	_logger = None
	_config = None

	def __new__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(System, cls).__new__(cls)
		return cls._instances[cls]

	@classmethod
	def _ini_config(cls):

		with open(os.path.dirname(__file__).split('source')[0] + 'config.json', 'r') as file:
			config = json.load(file)

		config['colors'] = {
			'c': colorama.Fore.CYAN,
			'g': colorama.Fore.GREEN,
			'm': colorama.Fore.MAGENTA,
			'r': colorama.Fore.RED,
			'y': colorama.Fore.YELLOW,
			'x': colorama.Style.RESET_ALL,
		}

		return config

	@classmethod
	def set_logger(cls):

		colors = cls.get_config()['colors']
		colorama.init(autoreset=True)

		class LogFormatter(logging.Formatter):

		    level = {
		        'DEBUG': colors['c'],
		        'INFO': colors['g'],
		        'WARNING': colors['y'],
		        'ERROR': colors['r'],
		        'CRITICAL': colors['m']
		    }

		    def format(self, record):

		        levelname = record.levelname
		        levelname_color = self.level.get(levelname, colorama.Fore.RESET)
		        record.levelname = f'{levelname_color}{levelname}{colorama.Fore.RESET}'
		        record.msecs = str(int(record.msecs)).zfill(3)
	
		        for k in colors:
		        	if '$'+k in record.msg:
		        		record.msg = record.msg.replace('$'+k, colors[k])

		        return super(LogFormatter, self).format(record)


		logger = logging.getLogger('SYS')
		logger.setLevel(logging.DEBUG)

		handler = logging.StreamHandler()
		formatter = LogFormatter('%(asctime)s.%(msecs)s [%(levelname)s] %(name)s: %(message)s', datefmt='%H:%M:%S')

		handler.setFormatter(formatter)
		logger.addHandler(handler)

		return logger

	@classmethod
	def get_logger(cls):
		if cls._logger is None:
			cls._logger = cls.set_logger()
		return cls._logger

	@classmethod
	def get_config(cls):
		if cls._config is None:
			cls._config = cls._ini_config()
		return cls._config