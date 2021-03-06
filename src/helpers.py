import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

import sound

def makeUVector2(pair1=(0, 0), pair2=(0, 0)):
	return cegui.UVector2(cegui.UDim(pair1[0], pair1[1]), cegui.UDim(pair2[0], pair2[1]))

def makeUVector2Scale(x=0, y=0):
	return cegui.UVector2(cegui.UDim(x, 0), cegui.UDim(y, 0))

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
	return wm.getWindow(name)

def bindEvent(name, object, method, event):
	"""Shortcut for binding a CEGUI widget event to a method"""
	wm = cegui.WindowManager.getSingleton()
	win = wm.getWindow(name)
	win.subscribeEvent(event, object, method)
	return win

def bindButtonEvent(name, object, method):
	window = bindEvent(name, object, method, cegui.PushButton.EventClicked)
	bindEvent(name, sound, "clickSound", cegui.PushButton.EventClicked)
	return window

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

def loadWindowLayout(name):
	"""Load window layout to work around API differences between CEGUI 0.5 and 0.6"""
	wm = cegui.WindowManager.getSingleton()
	if (hasattr(cegui, "Version__")):
		version = cegui.Version__
	else:
		version = cegui.CEGUI_version
	if version == '0.6.0':
		return wm.loadWindowLayout(name, False)
	else:
		return wm.loadWindowLayout(name)

