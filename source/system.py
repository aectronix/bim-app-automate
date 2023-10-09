import json
import os

class System:
	_instances = {}

	def __new__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(System, cls).__new__(cls)
			cls._instances[cls].config = cls._instances[cls].getConfig()
		return cls._instances[cls]


	def getConfig(self):

		with open(os.path.dirname(__file__).split('source')[0] + 'config.json', 'r') as file:
			config = json.load(file)

		return config