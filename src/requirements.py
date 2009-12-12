# This file checks you have installed the requirements for tpclient-pyogre 
# It can be run as standalone but is also run by the client at startup

import sys
sys.path.insert(0, '.')
import os.path

modules = ["libtpproto-py", "libtpclient-py", "schemepy"]
for module in modules:
	if os.path.exists(module):
		sys.path.insert(0, module)

import version
if os.path.exists(os.path.join("..", ".git")):
	os.chdir("..")
	for module in modules:
		if os.path.exists(os.path.join("src", module)) and not os.path.exists(os.path.join("src", module, ".git")):
			os.system("git submodule init")
	os.system("git submodule update")
	os.chdir("src")

notfound    = []
recommended = []

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

def tostr(ver1):
	s = ""
	for a in ver1:
		s += "."+str(a)
	return s[1:]

print "Client information:"
print "---------------------------------------------------------------"
import version
#try:
	#print "Client version", version.version_str+'+'+version.version_target_str, "(git %s)" % version.version_git
#except AttributeError:
print "Client version", version.version_str
print "Running from ", os.path.dirname(os.path.join(os.path.abspath(__file__)))
print

print "Checking requirements:"
print "---------------------------------------------------------------"

ogre_version = "1.6.1"
try:
	import ogre.renderer.OGRE as ogre
	print "Installed in ", ogre.__file__
	if hasattr(ogre, "Version__"):
		if ogre.Version__ < ogre_version:
			notfound.append("python-ogre/ogre == " + ogre_version)
	else:
		if ogre.ogre_version < ogre_version:
			notfound.append("python-ogre/ogre == " + ogre_version)
except ImportError, e:
	print e
	notfound.append("python-ogre/ogre")

try:
	import ogre.gui.CEGUI as cegui
except ImportError, e:
	print e
	notfound.append("python-ogre/cegui")

try:
	import pyglet
except ImportError, e:
	print e
	reason = "Pyglet, which is required for audio, does not seem to be installed"
	notfound.append(("pyglet", reason))

netlib_version = (0, 2, 99)
try:
	import tp.netlib

	print "Thousand Parsec Protocol Library Version", tp.netlib.__version__ 
	try:
		print "    (installed at %s)" % tp.netlib.__installpath__
	except AttributeError:
		print "    (version too old to work out install path)"

	try:
		from tp.netlib.version import version_git
		print "    (git %s)" % version_git
	except ImportError:
		print

	if cmp(netlib_version, tp.netlib.__version__) > 0:
		raise ImportError("Thousand Parsec Network Library (libtpproto-py) is too old")

except (ImportError, KeyError, AttributeError), e:
	print e
	notfound.append("tp.netlib >= " + tostr(netlib_version))

client_version = (0, 3, 99)
try:
	import tp.client

	print "Thousand Parsec Client Library Version", tp.client.__version__
	try:
		print "    (installed at %s)" % tp.client.__installpath__
	except AttributeError:
		print "    (version too old to work out install path)"
	
	try:
		from tp.client.version import version_git
		print "    (git %s)" % version_git
	except ImportError:
		print

	if cmp(client_version, tp.client.__version__) > 0:
		raise ImportError("Thousand Parsec Client Library (libtpclient-py) is too old")
except (ImportError, KeyError, AttributeError), e:
	print e
	notfound.append("tp.client >= " + tostr(client_version))

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

print
print "Checking locations:"
print "---------------------------------------------------------------"
import os
try:
	graphicsdir = os.environ["TPCLIENT_MEDIA"]
except KeyError:
	graphicsdir = '../media'
print "Media files are in %s" % graphicsdir
if not os.path.exists(os.path.join(graphicsdir, 'icons/icon.ico')):
	print "Can not find media required by this client."
	sys.exit()

try:
	windir = os.environ["TPCLIENT_WINDOW"]
except KeyError:
	windir = '../windows'
print "Window layouts are in %s" % windir
if not os.path.exists(os.path.join(windir, 'system.layout')):
	print "Can not find window layouts required by this client."
	sys.exit()

if len(notfound) > 0:
	print "The following requirements where not met"
	for module in notfound:
		print notfound

	import sys
	sys.exit(1)

import os, pprint
try:
	COLS = int(os.environ["COLUMNS"])
except (KeyError, ValueError):
	try:
		import struct, fcntl, sys, termios
		COLS = struct.unpack('hh', fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, '1234'))[1]
	except:
		COLS = 80

ALIGN = 25
if len(recommended) > 0:
	print "The following recommended modules where not found:"
	for module, reason in recommended:
		lines = [""]
		lines[-1] += '    %s, ' % module
		lines[-1] += ' ' * (ALIGN-len(lines[-1]))

		for word in reason.split(" "):
			if (len(lines[-1]) + len(word) + 2) > COLS:
				lines.append(' '*ALIGN)

			lines[-1] += word + " "

		print
		print "\n".join(lines)

