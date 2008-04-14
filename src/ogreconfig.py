import os

plugins = [
		"RenderSystem_GL",
		"Plugin_ParticleFX",
		"Plugin_BSPSceneManager",
		"Plugin_OctreeSceneManager",
		"Plugin_CgProgramManager"
	]

def generate_config():
	"""Generates a set of ogre config files"""
	if os.name.startswith("posix"):
		posix_config()
	elif os.name.startswith("nt"):
		nt_config()

def posix_config():
	try:
		f = open("plugins.cfg", "w")
		f.write("PluginFolder="+os.path.expanduser("~")+"/development/root/usr/lib/OGRE")
		f.write("\n")
		for plugin in plugins:
			f.write("Plugin="+plugin)
			f.write("\n")
	finally:
		f.close()

def nt_config():
	try:
		f = open("plugins.cfg", "w")
		drive = os.path.splitdrive(os.getcwd())[0]
		f.write("PluginFolder=" + os.path.join(drive, "PythonOgre", "plugins"))
		f.write("\n")
		for plugin in plugins:
			f.write("Plugin="+plugin+".dll")
			f.write("\n")
	finally:
		f.close()

