from distutils.core import setup
import py2exe, sys

sys.path.append('../dlls')

setup(
	console = ['tpclient-pyogre'],
	data_files = [
		('.' ,['ogre.cfg', 'plugins.cfg', 'resources.cfg',
		'../dlls/CEGUIExpatParser.dll', '../dlls/CEGUIFalagardWRBase.dll', 
		'../dlls/CEGUITinyXMLParser.dll'])
	],
	options={
			"py2exe": {
				"dll_excludes": [], 
				"packages": ["tp.netlib", "tp.client"], 
				"excludes": ["Tkconstants", "Tkinter", "tcl", "pydoc" ],
				"optimize": 2,
				"compressed": 0,
				"dist_dir": "../bin"
			}
		}
)
