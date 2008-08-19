import settings

try:
	from ogre.sound.OgreAL import *
	settings.sound_support = True
except ImportError, e:
	print e
	settings.sound_support = False

