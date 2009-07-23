import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

import helpers

class GUIFadeListener(ogre.FrameListener):
	""" Fades GUI in/out """

	def __init__(self):
		ogre.FrameListener.__init__(self)
		self.elements = {}
		self.child_map = {}
		self.wm = cegui.WindowManager.getSingleton()

	def registerElement(self, element, min_alpha=0.01, fadeout_time=1.0, fadein_time=1.0):
		window = self.wm.getWindow(element)
		cur_alpha = window.getAlpha()
		self.elements[element] = {'min_alpha':min_alpha,
							'max_alpha':cur_alpha,
							'cur_alpha':cur_alpha,
							'alpha_step_in':(cur_alpha-min_alpha)/fadein_time,
							'alpha_step_out':(cur_alpha-min_alpha)/fadeout_time,
							'active':True,
							'direction':'out',
							'event':True}
		helpers.bindEvent(element, self, "show", cegui.Window.EventMouseEnters)
		helpers.bindEvent(element, self, "hide", cegui.Window.EventMouseLeaves)
		self.bindChildren(element, element)

	def bindChildren(self, name, base):
		window = self.wm.getWindow(name)
		num_children = window.getChildCount()
		for i in range(num_children):
			child = window.getChildAtIdx(i)
			child_name = child.getName().c_str()
			self.child_map[child_name] = base
			helpers.bindEvent(child_name, self, "show", cegui.Window.EventMouseEnters)
			helpers.bindEvent(child_name, self, "hide", cegui.Window.EventMouseLeaves)
			self.bindChildren(child_name, base)

	def show(self, evt, event_call=True):
		if isinstance(evt, str):
			element = evt
		else:
			element = evt.window.getName().c_str()
		if element in self.child_map:
			element = self.child_map[element]
		self.elements[element]['active'] = True
		self.elements[element]['event'] = event_call
		self.elements[element]['direction'] = 'in'

	def hide(self, evt, event_call=True):
		if isinstance(evt, str):
			element = evt
		else:
			element = evt.window.getName().c_str()
		if element in self.child_map:
			element = self.child_map[element]
		self.elements[element]['active'] = True
		self.elements[element]['event'] = event_call
		self.elements[element]['direction'] = 'out'

	def frameStarted(self, evt):
		for element in self.elements:
			properties = self.elements[element]
			if properties['active']:
				if properties['direction'] == 'in':
					delta_alpha = properties['alpha_step_in'] * evt.timeSinceLastFrame
					alpha = properties['cur_alpha']+delta_alpha
					if alpha >= properties['max_alpha']:
						alpha = properties['max_alpha']
						properties['active'] = False
						if not properties['event']:
							self.hide(element)
					self.wm.getWindow(element).setAlpha(alpha)
					properties['cur_alpha'] = alpha
				elif properties['direction'] == 'out':
					delta_alpha = properties['alpha_step_out'] * evt.timeSinceLastFrame
					alpha = properties['cur_alpha']-delta_alpha
					if alpha < properties['min_alpha']:
						alpha = properties['min_alpha']
						properties['active'] = False
						if not properties['event']:
							self.show(element)
					self.wm.getWindow(element).setAlpha(alpha)
					properties['cur_alpha'] = alpha

		return ogre.FrameListener.frameStarted(self, evt)

