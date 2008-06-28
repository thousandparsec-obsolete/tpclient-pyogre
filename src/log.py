import ogre.renderer.OGRE as ogre

class Logger(ogre.LogListener):

	def __init__(self):
		ogre.LogListener.__init__(self)

	def messageLogged(self, message, level, debug, logName):
		pass
