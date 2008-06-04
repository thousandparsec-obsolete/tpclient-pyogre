import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

def setWidgetText(name, text):
	"""Shortcut for setting CEGUI widget text.

	Examples of widget text are window titles, edit box text and button captions.
	"""
	wm = cegui.WindowManager.getSingleton()
	wm.getWindow(name).setText(text)

def bindEvent(name, object, method, event):
	"""Shortcut for binding a CEGUI widget event to a method"""
	wm = cegui.WindowManager.getSingleton()
	wm.getWindow(name).subscribeEvent(event, object, method)

def pickle_dump(target_object, name="pickle"):
	import pickle
	try:
		f = open("%s_dump" % name, 'w')
		pickle.dump(target_object, f)
	except pickle.PicklingError:
		print "Pickle Error!"
	finally:
		f.close()

def pickle_load(name="pickle"):
	import pickle
	return_object = None
	try:
		f = open("%s_dump" % name, 'r')
		return_object = pickle.load(f)
	finally:
		f.close()
	return return_object

