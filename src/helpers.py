import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

def toggleWindow(name, visible=None):
	"""Toggles the visibility of a window.

	visible - Optional parameter to explicitly set visibility.

	Returns the window that was changed

	"""
	wm = cegui.WindowManager.getSingleton()
	if visible is None:
		visible = not wm.getWindow(name).isVisible()
	window = wm.getWindow(name)
	window.setVisible(visible)
	return window

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

def setWindowProperty(name, property, value):
	wm = cegui.WindowManager.getSingleton()
	wm.getWindow(name).setProperty(str(property), str(value))

def setupRadioButtonGroup(pair, group_id, id_array=None, select=0):
	wm = cegui.WindowManager.getSingleton()
	for i in range(len(pair)):
		radio_button = wm.getWindow(pair[i])
		radio_button.setGroupID(group_id)
		if i == select:
			radio_button.setSelected(True)
		if id_array:
			radio_button.setID(id_array[i])

def copyWindow(window, prefix):
	wm = cegui.WindowManager.getSingleton()
	old_name = window.name.c_str()
	old_name = old_name[old_name.rfind('/')+1:]
	name = prefix + "/" + old_name
	#print "cloning", name
	clone_window = wm.createWindow(window.type, name)
	copyWindowProperties(window, clone_window)

	for i in range(window.ChildCount):
		child = window.getChildAtIdx(i)
		if "__auto" not in child.name.c_str():
			clone_child = copyWindow(child, name)
			clone_window.addChildWindow(clone_child)

	return clone_window

def copyWindowProperties(window, clone):
	properties = ['Font', 'UnifiedMaxSize', 'TitlebarEnabled',
			'UnifiedAreaRect', 'CloseButtonEnabled', 'Text',
			'MaxTextLength', 'HorzFormatting', 'SizingEnabled', 'ClippedByParent']
	for p in properties:
		if window.isPropertyPresent(p):
			#print "setting", p, window.getProperty(p)
			clone.setProperty(p, window.getProperty(p))

def pickle_dump(target_object, name="pickle"):
	import pickle
	try:
		f = open("%s_dump" % name, 'w')
		pickle.dump(target_object, f)
	except pickle.PicklingError, e:
		print "Pickle Error:", e
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

