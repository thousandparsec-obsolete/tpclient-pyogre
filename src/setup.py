#!/usr/bin/env python

import shutil
import sys

import glob
import os.path

from setuptools import setup

from version import version
version = ("%s.%s.%s" % version) 
print "Version is %s" % version

arguments = dict(
	# Meta data
	name="tpclient-pyogre",
	version=version,
	license="GPL",
	description="Python-Ogre based client for Thousand Parsec",
	author="Tim Ansell, Eugene Tan",
	author_email="tim@thousandparsec.net, jmingtan@gmail.com",
	url="http://www.thousandparsec.net",
	# Files to include
	scripts=["tpclient-pyogre"],
	packages=[ \
		'.',
		],
	data_files=[(".", ("resources.cfg", )), ],
)

if sys.platform.startswith('linux') and "install" in sys.argv:
	import os, shutil

	# Clean up locally
	os.system('rm `find -name \*.pyc`')

	def makedirs(s):
		try:
			os.makedirs(s)
		except OSError, e:
			if e.errno != 17:
				raise
		return

	prefix = "/usr/local"
	temp   = None

	if "--prefix" in sys.argv:
		prefix = sys.argv[sys.argv.index('--prefix')+1]
	if "--temp" in sys.argv:
		temp = sys.argv[sys.argv.index('--temp')+1]
	for arg in sys.argv:
		if arg.startswith('--prefix='):
			trash, prefix = arg.split('=')
		elif arg.startswith('--temp='):
			trash, temp = arg.split('=')

	include_support = "--include-support" in sys.argv

	# If temp was not set, it should just be the prefix
	if temp is None:
		temp = prefix

	print "Installing to...", temp
	print "Target     is...", prefix

	# Documentation goes to
	#########################################################################
	docpath_temp  = os.path.join(temp,   "share/doc/tpclient-pywx")
	docpath       = os.path.join(prefix, "share/doc/tpclient-pywx")
	print 'docpath', docpath, "(copying to %s)" % docpath_temp

	makedirs(docpath_temp)
	docfiles = ['AUTHORS', 'doc/COPYING', 'LICENSE', 'doc/tips.txt']
	for file in docfiles:
		shutil.copy2(file, docpath_temp)

	# Locale files
	#########################################################################
	localepath_temp = os.path.join(temp,   "share/locale/%s/LC_MESSAGES/")
	localepath      = os.path.join(prefix, "share/locale/%s/LC_MESSAGES/")
	print 'localepath', localepath, "(copying to %s)" % localepath_temp

	for dir in os.listdir('locale'):
		if os.path.isfile(os.path.join('locale', dir)):
			continue
		print "Installing language files for %s" % dir

		llocalepath = localepath_temp % dir
		makedirs(llocalepath)
		shutil.copy2(os.path.join('locale', dir, 'tpclient-pywx.mo'), llocalepath)

	# Graphics files
	#########################################################################
	graphicspath_temp = os.path.join(temp,   "share/tpclient-pywx/graphics")
	graphicspath      = os.path.join(prefix, "share/tpclient-pywx/graphics") 
	print 'graphicspath', graphicspath, "(copying to %s)" % graphicspath_temp

	if os.path.exists(graphicspath_temp):
		shutil.rmtree(graphicspath_temp)
	shutil.copytree('graphics', graphicspath_temp)

	# Private python file
	#########################################################################
	codepath_temp = os.path.join(temp,   "share/tpclient-pywx")
	codepath      = os.path.join(prefix, "share/tpclient-pywx")
	print 'librarypath', codepath, "(copying to %s)" % codepath_temp

	try:
		makedirs(codepath_temp)
	except OSError:
		pass

	privatefiles = ['tpclient-pywx', 'version.py', 'requirements.py', 'utils.py', 'windows', 'extra']
	for file in privatefiles:
		if os.path.isfile(file):
			shutil.copy2(file, codepath_temp)
		if os.path.isdir(file):
			p = os.path.join(codepath_temp, file)
			if os.path.exists(p):
				shutil.rmtree(p)
			shutil.copytree(file, p)

	# Fix the version path
	os.system('python version.py --fix > %s' % os.path.join(codepath_temp, 'version.py'))

	# Cleanup some files which shouldn't have been copied...
	cleanupfiles = ['windows/xrc/generate.sh', 'windows/xrc/tp.pjd', 'windows/xrc/tp.xrc']
	for file in cleanupfiles:
		os.unlink(os.path.join(codepath_temp, file))

	# Create the startup script
	tpin = open(os.path.join('doc', 'tp-pywx-installed'), 'rb').read()
	tpin = tpin.replace("$$CODEPATH$$",     codepath)
	tpin = tpin.replace("$$GRAPHICSPATH$$", graphicspath)
	tpin = tpin.replace("$$DOCPATH$$",      docpath)

	tpout = open(os.path.join(codepath_temp, 'tp-pywx-installed'), 'wb')
	tpout.write(tpin)
	tpout.close()
	os.chmod(os.path.join(codepath_temp, 'tp-pywx-installed'), 0755)


	# Executables
	binpath_temp = os.path.join(temp,   "bin")
	binpath      = os.path.join(prefix, "bin")

	print 'binpath', binpath, "(copying to %s)" % binpath_temp
	makedirs(binpath_temp)
	
	binp = os.path.join(binpath_temp, 'tpclient-pywx')
	if os.path.exists(binp):
		os.unlink(binp)
	os.symlink(os.path.join(codepath, 'tp-pywx-installed'), binp)

	print "Client installed!"

	sys.exit()

if not "py2app" in sys.argv and not "py2exe" in sys.argv:
	print "This file is only provided to do the following,   (python setup.py py2exe)"
	print "  producing py2exe executable bundles for windows (python setup.py py2app)"
	print "  producing py2app dmg packages for Mac OS X      (python setup.py install)"
	print "  installing (a release) on a unix system"
	if os.path.exists(".git"):
		print
		print "WARNING!!"
		print " You seem to be running a git checkout (hence you don't want to be running this file)."
		print " tpclient-pywx can be run straight from this directory by just typing:"
		print "  ./tpclient-pywx"

	sys.exit()

if sys.platform == 'darwin':
	import py2app

	from setuptools import find_packages
	print find_packages()

	# Fix the version path
	os.system('git checkout version.py')
	os.system('python version.py --fix > %s' % 'version.py.tmp')
	os.unlink('version.py')
	os.rename('version.py.tmp', 'version.py')

	shutil.copy('tpclient-pywx', 'tpclient-pywx.py')

	arguments['scripts']=["tpclient-pywx.py"]
	
	# Py2App stuff
	extra_arguments = dict(
		app=["tpclient-pywx.py"],
		options = { 
			"py2app": {
				"argv_emulation": True,
				"compressed" : True,
				"strip"		: False,
				"optimize"	: 2,
				"packages"	: find_packages(),
				"includes"	: [],
				"excludes"	: ['Tkconstants', 'Tkinter', 'tcl', 'pydoc', 'pyreadline',
					'numpy.numarray', 'numpy.oldnumeric',
					'numpy.distutils', 'numpy.doc', 'numpy.f2py', 'numpy.fft', 'numpy.lib.tests', 'numpy.testing'],
				"resources"	: arguments['data_files'],
				"iconfile"	: "graphics/tp.icns",
				"plist"		: {
					"CFBundleSignature": "tppy",
					"CFBundleIdentifier": "net.thousandparsec.client.python.wx",
					"CSResourcesFileMapped": True,
					"CFBundleIconFile":	"tp.icns",
					"CFBundleGetInfoString": "Thousand Parsec wxPython Client %s" % version, 
					"CFBundleName": "tpclient-pywx",
					"CFBundleShortVersion": version,
					"CFBundleURLTypes": {
						"CFBundleTypeRole": "Viewer",
						"CFBundleURLIconFile": "tp.icns",
						"CFBundleURLName": "Thousand Parsec URI",
						"CFBundleURLSchemes": ["tp", "tps", "tp-http", "tp-https",],
					},
					"LSMinimumSystemVersion": "10.3.9",
#					"LSUIPresentationMode": 1,
				}
			}
		}
	)

elif sys.platform == 'win32':
	import py2exe

	dist_folder = os.path.join("..", "bin")
	if os.path.exists(dist_folder):
		shutil.rmtree(dist_folder)

	# Py2EXE stuff
	extra_arguments = dict(
		windows=[{
			"script": "tpclient-pyogre",
			"icon_resources": [(1, "../media/icons/icon.ico")],
		}],
		options={
			"py2exe": {
				"dll_excludes": [ "MSVCP80.dll", "MSVCR80.dll" ], 
				"packages": ["tp.netlib", "tp.client"], 
				"excludes": ["Tkconstants", "Tkinter", "tcl", "pydoc"],
				"optimize": 2,
				"compressed": 0,
				"dist_dir": dist_folder,
			}
		}, 
	)

	# Link the dlls folder for those hard to find dlls
	#sys.path.append(os.path.join("..", "dlls"))

	# Attempt to find dlls from system directories
	import ogre.renderer.OGRE as ogre
	ogre_path = os.path.dirname(ogre.__file__)
	arguments["data_files"].append(os.path.join(ogre_path, "boost_python-vc80-mt-1_35.dll"))

	import ogre.gui.CEGUI as cegui
	cegui_path = os.path.dirname(cegui.__file__)
	arguments["data_files"].append(os.path.join(cegui_path, "CEGUIExpatParser.dll"))
	arguments["data_files"].append(os.path.join(cegui_path, "CEGUIFalagardWRBase.dll"))

	import ogre.sound.OgreAL as ogreal
	ogreal_path = os.path.dirname(ogreal.__file__)
	arguments["data_files"].append(os.path.join(ogreal_path, "wrap_oal.dll"))

else:
	print "You shouldn't be running this (as it's only for Mac or Windows maintainers).."
	sys.exit()

arguments.update(extra_arguments)
setup(**arguments)

# Post compilation stuff
if sys.platform == 'darwin':
	if "py2app" in sys.argv:
		basedir = os.path.join("dist", "tpclient-pywx.app", "Contents")

		# Need to do some cleanup because the modulegraph is a bit brain dead
		base = os.path.join(basedir, "Resources", "lib", "python2.5")
		for i in (
				"xrc", "main", "overlays", "wxFloatCanvas", "Utilities", # local excesses
				"netlib", "objects", "ObjectExtra", "OrderExtra", "support", "discover", "pyZeroconf", 
				"client", "pyscheme", "discover", 
				# Numpy, numpy, numpy
				"numpy/oldnumeric", "numpy/numarray", "numpy/doc", "numpy/lib/tests", "numpy/distutils"
				"numpy/core/tests",
				):
			p = os.path.join(base, i)
			if os.path.exists(p):
				print "Removing", p
				shutil.rmtree(p)


		# Remove the pyscheme tests
		pyschemet = os.path.join(base, "tp", "client", "pyscheme", "t")
		if os.path.exists(pyschemet):
			shutil.rmtree(pyschemet)

		# Need to clean up any .py$ files which got included for some unknown reason...
		# Need to clean up any .pyc$ when a .pyo$ exists too
		for line in os.popen('find %s -name \*.pyc' % basedir).xreadlines():
			py = line.strip()[:-1]
			pyc = py+'c'
			pyo = py+'o'
			if os.path.exists(py):
				print "Removing %s as %s exists" % (py, pyo)
				os.unlink(py)

			if "numpy" in line:
				continue

			if os.path.exists(pyo):
				print "Removing %s as %s exists" % (pyc, pyo)
				os.unlink(pyc)


		# Clean up any ~ which got wrongly copied in..
		for line in os.popen('find %s -name \*~' % basedir).xreadlines():
			os.unlink(line.strip())

	# Create a package
	dmg = "tpclient-pywx_%s.dmg" % version
	if os.path.exists(dmg):
		os.unlink(dmg)

	print "Creating dmg package"
	os.system("cd doc/mac/; chmod a+x pkg-dmg make-diskimage; ./make-diskimage ../../%s  ../../dist tpclient-pywx -null- dstore background.jpg ../../graphics/tp.icns" % dmg)

	# Restore the version.py back to the git version...
	os.system('git checkout version.py')

elif sys.platform == 'win32':
	if os.path.exists("build"):
		shutil.rmtree("build")

	dest_plugins = os.path.join(dist_folder, "plugins")

	# Get plugins from plugins.cfg
	plugin_cfg = "plugins.cfg"
	if os.path.exists(plugin_cfg):
		try:
			f = open("plugins.cfg", "r")
			plugin_folder = f.readline().split("=")[1].strip()
			plugins = []
			for line in f:
				plugins.append(line.split("=")[1].strip())
		finally:
			f.close()
		
		os.mkdir(dest_plugins)
		for plugin in plugins:
			src = os.path.join(plugin_folder, plugin)
			dest = os.path.join(dest_plugins, plugin)
			shutil.copy(src, dest)

	# Alternatively, attempt to find plugins in parent folder
	if not os.path.exists(dest_plugins):
		plugins = os.path.join("..", "plugins")
		if os.path.exists(plugins):
			shutil.copytree(plugins, dest_plugins)

	# We should now use upx on the executables to make em smaller.
	extensions = ('pyd', 'dll', 'exe')
	folders = (dist_folder, dest_plugins)
	for extension in extensions:
		for folder in folders:
			path = os.path.join(folder, "*" + extension)
			os.system("upx --best %s" % path)

	# Should run NSIS now.
	os.chdir("..")
	os.system("makensis setup.nsi")
