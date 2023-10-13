import colorama
import json
import logging
import os

class System:
	_instances = {}

	def __new__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(System, cls).__new__(cls)
			cls._instances[cls].config = cls._instances[cls].getConfig()
			cls._instances[cls].logger = cls._instances[cls].getLogger('SYS')
		return cls._instances[cls]


	def getConfig(self):

		with open(os.path.dirname(__file__).split('source')[0] + 'config.json', 'r') as file:
			config = json.load(file)

		return config


	def getLogger(self, name):

		self.config['colors'] = {
			'c': colorama.Fore.CYAN,
			'g': colorama.Fore.GREEN,
			'm': colorama.Fore.MAGENTA,
			'r': colorama.Fore.RED,
			'y': colorama.Fore.YELLOW,
			'x': colorama.Style.RESET_ALL,
		}

		class LogFormatter(logging.Formatter):

		    level = {
		        'DEBUG': self.config['colors']['c'],
		        'INFO': colorama.Fore.GREEN,
		        'WARNING': colorama.Fore.YELLOW,
		        'ERROR': colorama.Fore.RED,
		        'CRITICAL': colorama.Fore.MAGENTA,
		    }

		    def format(self, record):
		        levelname = record.levelname
		        levelname_color = self.level.get(levelname, colorama.Fore.RESET)
		        record.levelname = f'{levelname_color}{levelname}{colorama.Fore.RESET}'
		        return super(LogFormatter, self).format(record)

		c = colorama
		c.init(autoreset=True)

		logger = logging.getLogger(name)
		logger.setLevel(logging.DEBUG)

		handler = logging.StreamHandler()
		formatter = LogFormatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s', datefmt='%H:%M:%S')

		handler.setFormatter(formatter)
		logger.addHandler(handler)

		return logger

