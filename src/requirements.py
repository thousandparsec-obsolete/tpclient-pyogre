# This file checks you have installed the requirements for tpclient-pyogre 
# It can be run as standalone but is also run by the client at startup

import sys
import os.path

notfound = []

def configpath():
	"""\
	Figures out where to save the preferences.
	"""
	dirs = [("APPDATA", "Thousand Parsec"), ("HOME", ".tp"), (".", "var")]
	for base, extra in dirs:
		if base in os.environ:
			base = os.environ[base]
		elif base != ".":
			continue
			
		rc = os.path.join(base, extra)
		if not os.path.exists(rc):
			os.mkdir(rc)
		return rc

class FileOutput(object):
	def __init__(self, stdout=None):
		self.o = stdout

		self.f = open(os.path.join(configpath(), "tpclient-pyogre.log"), "wb")
		if not self.o is None:
			self.o.write("Output going to %s\n" % self.f.name)

	def write(self, s):
		if isinstance(s, unicode):
			s = s.encode('utf-8')

		if not self.o is None:
			self.o.write(s)
		self.f.write(s)
	
	def __del__(self):
		if not self.o is None:
			import os
			os.unlink(self.f.name)

if hasattr(sys, "frozen"):
	sys.stdout = FileOutput()
	sys.stderr = sys.stdout
else:
	sys.stdout = FileOutput(sys.stdout)
	sys.stderr = sys.stdout

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

try:
	import os
	if not os.path.exists("./plugins.cfg"):
		import ogreconfig
		ogreconfig.generate_config()
except Exception, e:
	print e
	notfound.append("local config files")

if len(notfound) > 0:
	print "The following requirements where not met"
	for module in notfound:
		print notfound

	import sys
	sys.exit(1)
