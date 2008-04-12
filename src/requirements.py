# This file checks you have installed the requirements for tpclient-pywx 
# It can be run as standalone but is also run by the client at startup

notfound = []

try:
	import ogre.renderer.OGRE as ogre
except ImportError:
	notfound.append("python-ogre")

try:
	import ogre.gui.CEGUI as cegui
except ImportError:
	notfound.append("python-ogre/cegui")

try:
	import tp.netlib
except ImportError:
	import sys
	sys.path.append("..")
	
	try:
		import tp.netlib
	except ImportError:
		notfound.append("tp.netlib")

try:
	import tp.client
except ImportError:
	notfound.append("tp.client")

import __builtin__
try:
	import gettext
	
	gettext.install("tpclient-pyogre")
	__builtin__._ = gettext.gettext	
except ImportError:
	def _(s):
		return s
	__builtin__._ = _

if len(notfound) > 0:
	print "The following requirements where not met"
	for module in notfound:
		print notfound

	import sys
	sys.exit(1)
