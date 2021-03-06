import os

plugins = [
		"RenderSystem_GL",
		"Plugin_ParticleFX",
		#"Plugin_BSPSceneManager",
		"Plugin_OctreeSceneManager",
		#"Plugin_CgProgramManager"
	]

default_windows_drive = "c:/"

def generate_config():
	"Generates a set of ogre config files"
	if os.name.startswith("posix"):
		posix_config()
	elif os.name.startswith("nt"):
		nt_config()

def posix_config():
	try:
		import ogre
		folder = ogre.__file__.partition('lib')
		folder = os.path.join(folder[0], 'lib', 'OGRE')

		f = open("plugins.cfg", "w")
		f.write("PluginFolder="+folder)
		f.write("\n")
		for plugin in plugins:
			f.write("Plugin="+plugin)
			f.write("\n")
	finally:
		f.close()

def nt_config():
	"Searches current directory for OGRE plugins, then the python-ogre directory in C:, and then in the current drive"
	try:
		f = open("plugins.cfg", "w")

		path = os.path.join(".", "plugins")
		if not os.path.exists(path):
			path = os.path.join("..", "plugins")
		if not os.path.exists(path):
			drive = default_windows_drive
			path = os.path.join(drive, "PythonOgre", "plugins")
		if not os.path.exists(path):
			drive = os.path.splitdrive(os.getcwd())[0] + "/"
			path = os.path.join(drive, "PythonOgre", "plugins")

		if os.path.exists(path):
			f.write("PluginFolder=" + path)
			f.write("\n")
			for plugin in plugins:
				f.write("Plugin="+plugin+".dll")
				f.write("\n")
			f.write("Plugin=RenderSystem_Direct3D9.dll")
			f.write("\n")
		else:
			print "Python Ogre not found"
	finally:
		f.close()

