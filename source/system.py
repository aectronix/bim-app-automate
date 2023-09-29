# Singleton method

class System:
	_instances = {}

	def __new__(cls, *args, **kwargs):
		if cls not in cls._instances:
			cls._instances[cls] = super(System, cls).__new__(cls)
		return cls._instances[cls]