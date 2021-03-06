import math
import random

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui
import ogre.io.OIS as ois
#import ogreal

from tp.netlib.objects import OrderDescs
from tp.netlib.objects.constants import *
from tp.netlib.objects import parameters
from tp.netlib import objects

import overlay
import starmap
import helpers
import gui
import settings
import sound
import tp_helpers
from tp.client import objectutils

UNIVERSE = 1
STAR = 2
PLANET = 3
FLEET = 4
WORMHOLE = 5

OBJECT = 1

class Scene(object):
	"""Displays a scene for the user.

	Can be swapped with other scenes using the show and hide methods.

	"""

	def __init__(self, parent, sceneManager):
		self.parent = parent
		self.guiSystem = parent.guiSystem
		self.sceneManager = sceneManager

		# Create the root for this Scene
		self.rootNode = sceneManager.getRootSceneNode().createChildSceneNode((0, 0, 0))
		self.camera = self.sceneManager.getCamera('PlayerCam')

		# Where to store any GUI windows
		self.windows = []

	def show(self):
		"""Called when this SceneManager is being displayed"""
		# Attach the root node
		self.sceneManager.getRootSceneNode().addChild(self.rootNode)

		# Show all the GUI windows for this scene
		for window in self.windows:
			window.show()

		# Restore properties
		self.sceneManager.ambientLight = self.ambientLight

		# Set the last saved camera position and orientation
		camera = self.sceneManager.getCamera( 'PlayerCam' )
		camera.position = self.position
		camera.orientation = self.orientation
		self.camera = camera

	def hide(self):
		"""Called when this SceneManager is no longer being displayed"""
		# Save camera position and orientation
		self.position = self.camera.position
		self.orientation = self.camera.orientation
		del self.camera

		# Save properties
		self.ambientLight = self.sceneManager.ambientLight

		# Hide all the GUI windows for this scene
		for window in self.windows:
			window.hide()

		# Detach the root node
		self.sceneManager.getRootSceneNode().removeChild(self.rootNode)

	def update(self, evt):
		"""Update is called every frame"""
		return True

	# Note, the GUI system always gets fed before the Scene does
	def mouseDragged(self, evt):
		return False

	def mousePressed(self, evt, id):
		return False

	def mouseReleased(self, evt, id):
		return False

	def mouseDragged(self, evt):
		return False

	def mouseMoved(self, evt):
		return False

	def keyPressed(self, evt):
		return False

	def keyReleased(self, evt):
		return False

	def keyDown(self, keyboard):
		return False

	def quit(self, evt=None):
		"""Quit the client"""
		self.parent.Cleanup()

class MenuScene(Scene):
	"""Menu Scenes all share a common backdrop

	The state of the background is preserved across Menu Scenes

	"""

	def setPosition(self, position):
		MenuScene.position = position
	position = property(fset=setPosition)

	def setOrientation(self, orientation):
		MenuScene.orientation = orientation
	orientation = property(fset=setOrientation)

	def show(self):
		Scene.show(self)
		self.sceneManager.setSkyBox(True, 'skybox/SpaceSkyBox')

	def hide(self):
		self.sceneManager.setSkyBox(False, '')
		Scene.hide(self)

	def update(self, evt):
		camera = self.sceneManager.getCamera('PlayerCam')
		camera.pitch(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame * 2)))
		camera.yaw(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame * -2)))

		return True

class LoginScene(MenuScene):
	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		# when populating a cegui list, must keep the references, otherwise segfault
		self.servers = []

		login = helpers.loadWindowLayout("login.layout")
		self.guiSystem.getGUISheet().addChildWindow(login)
		self.windows.append(login)
		self.login = login

		# key states
		self.tab_down = False
		self.enter_down = False

		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("Login/SaveDetails").setSelected(settings.save_details)
		if settings.user_name != None:
			wm.getWindow("Login/Username").setText(settings.user_name)
		if settings.password != None:
			wm.getWindow("Login/Password").setText(settings.password)
		if settings.previous_game != None:
			self.setServer(settings.previous_game)

		helpers.bindButtonEvent("Login/LoginButton", self, "onConnect")
		helpers.bindButtonEvent("Login/QuitButton", self, "quit")
		helpers.bindButtonEvent("Login/ConfigButton", self, "onConfig")
		helpers.bindEvent("Login/SaveDetails", self, "onSaveDetails", cegui.Checkbox.EventCheckStateChanged)

		helpers.bindButtonEvent("Message/OkButton", self, "onMessageOk")

		self.hide()

	def onSaveDetails(self, evt):
		settings.save_details = cegui.WindowManager.getSingleton().getWindow("Login/SaveDetails").isSelected()

	def onNetworkFailure(self, evt):
		print "NetworkFailure", evt

	def onFoundRemoteGame(self, evt):
		"""Called when a remote game is found from the metaserver"""
		print "found remote game"
		location = evt.game.locations["tp"][0][0]
		print location
		wm = cegui.WindowManager.getSingleton()
		combobox = wm.getWindow("Login/Server")
		item = cegui.ListboxTextItem(location)
		self.servers.append(item)
		combobox.addItem(item)

	def onConnect(self, evt=None):
		"""Called when user clicks on the login button"""
		wm = cegui.WindowManager.getSingleton()

		host = wm.getWindow("Login/Server").getText().c_str()
		username = wm.getWindow("Login/Username").getText().c_str()
		password = wm.getWindow("Login/Password").getText().c_str()

		settings.user_name = username
		settings.password = password
		settings.previous_game = host

		#print "onConnect", host, username, password
		self.parent.application.network.Call( \
				self.parent.application.network.ConnectTo, host, username, password, True)

	def onConfig(self, evt):
		"""Called when user clicks on the config button"""
		self.config = gui.ConfigWindow(self.login)

	def onMessageOk(self, evt):
		helpers.toggleWindow("Message", False)

	def showMessage(self, text):
		helpers.toggleWindow("Message", True).activate()
		helpers.setWidgetText("Message/Text", str(text))

	def setServer(self, host):
		"""Sets the initial value of the host input field"""
		helpers.setWidgetText("Login/Server", host)

	def tab(self, next=True):
		"""Rotates input focus through a set of editable widgets

		next - True sets focus to the next widget, False sets focus to the previous widget

		"""
		wm = cegui.WindowManager.getSingleton()
		tab_targets = [
				wm.getWindow("Login/Server"),
				wm.getWindow("Login/Username"),
				wm.getWindow("Login/Password"),
				]
		focus_found = False
		for target in tab_targets:
			if target.hasInputFocus():
				if next:
					index = tab_targets.index(target) + 1
					if index >= len(tab_targets):
						index = 0
				else:
					index = tab_targets.index(target) - 1
					if index < 0:
						index = len(tab_targets) - 1
				focus_found = True
				t = tab_targets[index]
				t.activate()
				t.setCaratIndex(len(t.getText().c_str()))
				break

		if not focus_found:
			t = tab_targets[0]
			t.activate()
			t.setCaratIndex(len(t.getText().c_str()))

	def keyDown(self, keyboard):
		if keyboard.isKeyDown(ois.KC_TAB):
			if not self.tab_down:
				if keyboard.isModifierDown(ois.Keyboard.Modifier.Shift):
					self.tab(False)
				else:
					self.tab()
				self.tab_down = True
		else:
			self.tab_down = False

		if keyboard.isKeyDown(ois.KC_RETURN):
			if not self.enter_down:
				self.onConnect()
				self.enter_down = True
		else:
			self.enter_down = False

class StarmapScene(MenuScene):
	"""Manages the GUI and Starmap class"""

	SELECTABLE = 1 << 0
	UNSELECTABLE = 1 << 1

	pan_speed = 500
	tolerance_delta = 1
	scroll_speed = 100
	low_fps_threshold = 15
	mouseover_timeout = 1000
	doubleclick_timeout = 1000
	distance_units = None

	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		self.mouse_delta = ogre.Vector2(0, 0)
		self.current_object = None
		self.created = False
		self.starmap = starmap.Starmap(self, self.sceneManager, self.rootNode)
		self.timeout = False
		self.remaining_time_timer = ogre.Timer()
		self.remaining_time = 0
		self.mouse_position = [0, 0]
		self.sounds = {}
		self.map_scale = 0;

		# TODO: Shift to info overlay class
		self.mouseover_timer = ogre.Timer()
		self.mouseover = None
		self.doubleclick_timer = ogre.Timer()
		self.singleclick = False

		# TODO: Shift to camera class
		self.camera_focus_node = self.rootNode.createChildSceneNode("CameraFocus")
		self.camera_node = self.camera_focus_node.createChildSceneNode("CameraNode")
		self.camera_node.attachObject(self.camera)
		self.camera_target_node = self.camera_focus_node.createChildSceneNode("CameraTarget")
		self.camera_target_node.position = self.camera_node.position
		self.camera.setQueryFlags(self.UNSELECTABLE)

		self.createGui()

		if settings.sound_support:
			from requirements import graphicsdir
			import pyglet
			import os
			import sound
			bg_file = os.path.join(graphicsdir, "sound/ambient.ogg")
			if os.path.exists(bg_file):
				bg_media = pyglet.media.load(bg_file)
				sound.bg.queue(bg_media)

		self.hide()

	def createGui(self):
		system = helpers.loadWindowLayout("system.layout")
		self.guiSystem.getGUISheet().addChildWindow(system)
		self.windows = [system]
		self.system = system

		helpers.bindButtonEvent("TopBar/MenuButton", self, "toggleMainMenu")
		helpers.bindButtonEvent("Windows/EndTurnButton", self, "requestEOT")
		helpers.bindEvent("Navigation/ZoomIn", self.starmap, "zoomIn", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Navigation/ZoomOut", self.starmap, "zoomOut", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Navigation/Deselect", self, "unselect", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Navigation/Center", self, "focus", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Navigation/Autofit", self.starmap, "autofit", cegui.Window.EventMouseButtonDown)

		self.message_window = gui.MessageWindow(self)
		self.design_window = gui.DesignsWindow(self)
		self.info_window = gui.InformationWindow(self)
		self.system_window = gui.SystemWindow(self)
		self.orders_window = gui.OrdersWindow(self)
		self.sub_windows = [
			self.message_window,
			self.design_window,
			self.info_window,
			self.system_window,
			self.orders_window,
			]

		wm = cegui.WindowManager.getSingleton()
		self.orders_menu = overlay.RadialMenu(self.camera)
		wm.getWindow("Starmap").addChildWindow(self.orders_menu.menu)

		self.information_overlay = overlay.InformationOverlay()
		wm.getWindow("Starmap").addChildWindow(self.information_overlay.overlay)

	def show(self):
		Scene.show(self)
		self.sceneManager.setSkyBox(True, 'skybox/SpaceSkyBox')
		self.starmap.show()
		if settings.music:
			import sound
			sound.bg.play()
			sound.music_list.append(sound.bg)

	def hide(self):
		Scene.hide(self)
		self.sceneManager.setSkyBox(False, '')
		self.starmap.hide()
		if settings.music:
			import sound
			if sound.bg in sound.music_list:
				sound.bg.pause()
				sound.music_list.remove(sound.bg)

	def calculateScale(self, objects):
		"""Calculate a reasonable scale from a list of objects"""
		closest = None
		lower_left = [0, 0]
		upper_right = [0, 0]
		for obj in objects:
			if obj._subtype is not STAR:
				continue
			x, y, z = tp_helpers.getAbsPosition(obj)

			if lower_left[0] > x:
				lower_left[0] = x
			if lower_left[1] > y:
				lower_left[1] = y
			if upper_right[0] < x:
				upper_right[0] = x
			if upper_right[1] < y:
				upper_right[1] = y

		print upper_right, lower_left, closest
		map_width = abs(abs(upper_right[0]) - lower_left[0])
		map_height = abs(abs(upper_right[1]) - lower_left[1])
		print map_width, map_height
		scale = math.hypot(map_width, map_height)
		return scale

	def getScaledPosition(self, position):
		"""Returns an array containing the position scaled accordingly"""
		return ogre.Vector3(
				(position[0] / self.map_scale) * self.distance_units,
				(position[1] / self.map_scale) * self.distance_units,
				(position[2] / self.map_scale) * self.distance_units,
				)

	def create(self, cache):
		"""Creates list of objects from cache"""
		print "creating the starmap"
		self.objects = cache.objects

		#self.starmap.createBackground()
		designs = self.getDesigns(cache)
		self.map_scale = self.calculateScale(self.objects.values())

		pan_speed = 100000000 / self.map_scale * settings.distance_units
		if pan_speed < self.pan_speed:
			pan_speed = self.pan_speed
		else:
			self.pan_speed = pan_speed
		self.scroll_speed = pan_speed / 5

		self.distance_units = settings.distance_units

		for object in self.objects.values():
			pos = self.getScaledPosition(tp_helpers.getAbsPosition(object))

			#print "creating", object.id, object.name, "\ttype:", object._subtype, "at", pos

			#if hasattr(object, "parent"):
				#print "parent of %s is %i" % (object.name, object.parent)

			if object._subtype is STAR:
				node = self.starmap.addStar(object, pos)

			if object._subtype is PLANET:
				# Get parent system and the number of other planets
				parent = self.updateObjectIndex(object, "planets", PLANET)
				if object.parent != 1 and self.starmap.hasObject(object.parent):
					pos = self.starmap.nodes[object.parent].position
				node = self.starmap.addPlanet(object, pos, parent)

			if object._subtype is FLEET:
				# Get parent system and the number of other fleets
				parent = self.updateObjectIndex(object, "fleets", FLEET)
				# Assign fleet type according to how many designs player has
				fleet_type = (object.Ships[0][0][0][1] - 1) % designs[tp_helpers.getOwner(object)]
				#print "ship_design: %i designs: %i fleet type: %i" % (object.Ships[0][0][0][0], designs[tp_helpers.getOwner(object), fleet_type)
				if object.parent != 1 and self.starmap.hasObject(object.parent):
					pos = self.starmap.nodes[object.parent].position
				node = self.starmap.addFleet(object, pos, parent, fleet_type, self.SELECTABLE)

			if object._subtype is WORMHOLE:
				end_pos = self.getScaledPosition(object.end)
				self.starmap.addWormHole(object, pos, end_pos)

		self.system_window.create(cache)
		self.message_window.create(cache)
		self.created = True
		if hasattr(self.objects[0], "turn"):
			helpers.setWidgetText("TopBar/Turn", "Turn %i" % self.objects[0].turn)
		self.starmap.updateMapExtents()
		self.starmap.autofit()
		self.starmap.updateBoundingBox()
		self.design_window.populateDesignsWindow(cache.designs)

	def updateObjectIndex(self, object, subtype_name, subtype_index):
		"""Finds how many siblings an object has and updates it's index accordingly

		object - The current object
		subtype_name - The name of the object type
		subtype_index - The index of the object type

		e.g. updateObjectIndex(object, "fleets", 4)

		"""
		parent = self.objects[object.parent]
		if not hasattr(parent, subtype_name) or not hasattr(object, "index"):
			exec("parent.%s = %i" % (subtype_name, 0))
			index = 1
			for i in self.objects.values():
				if i._subtype == subtype_index and i.parent == object.parent:
					i.index = index
					index += 1
					exec("parent.%s += 1" % subtype_name)
		return parent

	def getDesigns(self, cache):
		"""Get number of designs by each player"""
		designs = {}
		for design in cache.designs.values():
			if designs.has_key(design.owner):
				designs[design.owner] += 1
			else:
				designs[design.owner] = 1
		return designs

	def recreate(self, cache):
		"""Update locations of objects

		Assumes stars and planet locations do not change.

		"""
		print "Updating starmap"
		self.objects = cache.objects
		self.starmap.clearTempLines()
		designs = self.getDesigns(cache)

		for object in cache.objects.values():
			pos = self.getScaledPosition(tp_helpers.getAbsPosition(object))
			#print "updating", object.id, object.name, object._subtype, "at", pos

			if object._subtype is FLEET:
				# Get parent system and the number of other fleets
				# FIXME: What if a fleet is destroyed
				parent = self.updateObjectIndex(object, "fleets", FLEET)
				if object.parent != 1 and self.starmap.hasObject(object.parent):
					pos = self.starmap.nodes[object.parent].position

				if self.starmap.hasObject(object.id):
					self.starmap.setFleet(object, pos, parent)
				else:
					fleet_type = (object.Ships[0][0][0][0] - 1) % designs[tp_helpers.getOwner(object)]
					self.starmap.addFleet(object, pos, parent, fleet_type)

		if hasattr(self.objects[0], "turn"):
			helpers.setWidgetText("TopBar/Turn", "Turn %i" % self.objects[0].turn)

		self.starmap.updateMapExtents()
		self.starmap.updateBoundingBox()

	def update(self, evt):
		self.starmap.update()
		for i in range(settings.zoom_speed):
			self.updateCamera()

		if self.mouseover and self.mouseover_timer.getMilliseconds() > self.mouseover_timeout:
			self.information_overlay.show(self.mouseover, self.getCache())
			self.information_overlay.update(*self.mouse_position)

		if self.remaining_time > 0 and self.remaining_time_timer.getMilliseconds() >= 1000:
			self.remaining_time -= 1
			minutes = int(self.remaining_time / 60)
			seconds = int(self.remaining_time % 60)
			helpers.setWidgetText("Windows/EOT", "EOT: %i:%02i" % (minutes, seconds))
			self.remaining_time_timer.reset()
			if self.remaining_time < 10:
				helpers.setWindowProperty("Windows/EOT", "Alpha", 1)
			else:
				helpers.setWindowProperty("Windows/EOT", "Alpha", 0.5)

		#if self.parent.renderWindow.lastFPS < self.low_fps_threshold:
			#self.starmap.setIconView(True)
		return True

	def updateCamera(self):
		cam_pos = self.camera_node.position
		target_pos = self.camera_target_node.position

		if abs(cam_pos.x - target_pos.x) < self.pan_speed:
			self.camera_node.position.x = target_pos.x
		elif cam_pos.x < target_pos.x:
			self.camera_node.translate(self.pan_speed, 0, 0)
		elif cam_pos.x > target_pos.x:
			self.camera_node.translate(-self.pan_speed, 0, 0)

		if abs(cam_pos.y - target_pos.y) < self.pan_speed:
			self.camera_node.position.y = target_pos.y
		elif cam_pos.y < target_pos.y:
			self.camera_node.translate(0, self.pan_speed, 0)
		elif cam_pos.y > target_pos.y:
			self.camera_node.translate(0, -self.pan_speed, 0)

		if cam_pos.z != target_pos.z:
			self.starmap.updateZoom()
			if cam_pos.z < target_pos.z:
				self.camera_node.translate(0, 0, self.scroll_speed)
			else:
				self.camera_node.translate(0, 0, -self.scroll_speed)
		self.starmap.updateBackground(self.camera.getDerivedPosition())

	def onNetworkTimeRemaining(self, evt):
		"""Called whenever a NetworkTimeRemaining packet is received"""
		print "onNetworkTimeRemaining", evt.remaining
		self.remaining_time = evt.remaining
		minutes = int(self.remaining_time / 60)
		seconds = int(self.remaining_time % 60)
		helpers.setWidgetText("Windows/EOT", "EOT: %i:%02i" % (minutes, seconds))
		self.remaining_time_timer.reset()
		if self.remaining_time == 0:
			print "End of turn"
			helpers.setWindowProperty("Windows/EndTurnButton", "Alpha", 1)
			self.timeout = True
			network = self.parent.application.network
			network.Call(network.CacheUpdate)

	def onNetworkFailure(self, evt):
		"""Called whenever a NetworkFailure packet is received"""
		print "onNetworkFailure"

	def onCacheUpdate(self, evt):
		"""Called whever the cache is updated"""
		print "onCacheUpdate", evt
		cache = self.getCache()
		if self.created:
			if self.timeout:
				self.recreate(cache)
				self.timeout = False
			elif self.current_object:
				self.orders_window.update()
				id = self.getIDFromMovable(self.current_object)
				self.orders_window.updateOrdersWindow(id, cache)
		else:
			self.create(cache)

	def onCacheDirty(self, evt):
		print "OnCacheDirty", evt

	def requestEOT(self, evt):
		print "Requesting EOT"
		helpers.setWindowProperty("Windows/EndTurnButton", "Alpha", 0.5)
		network = self.parent.application.network
		network.Call(network.RequestEOT)

	def mousePressed(self, evt, id):
		#print self, "mousePressed"
		self.mouse_delta -= self.mouse_delta

	def mouseMoved(self, evt):
		"""Handles the MouseMoved event

		If the middle mouse button is down pan the screen.
		Scrolling the mousewheel will zoom in and out.

		"""
		if self.timeout:
			return False
		state = evt.get_state()

		self.mouse_delta += (abs(state.X.rel), abs(state.Y.rel))
		self.mouse_position = [state.X.abs, state.Y.abs]

		if state.buttonDown(ois.MB_Middle):
			if self.starmap.zoom_level != 0:
				adjusted_pan = abs(self.starmap.zoom_level)
			else:
				adjusted_pan = self.pan_speed
			self.starmap.pan(state.X.rel * adjusted_pan, -state.Y.rel * adjusted_pan)

		elif state.buttonDown(ois.MB_Right):
			self.starmap.rotate(state.X.rel, state.Y.rel)

		elif state.Z.rel < 0:
			self.starmap.zoom(2 * self.pan_speed)

		elif state.Z.rel > 0:
			self.starmap.zoom(-2 * self.pan_speed)

		x = float(state.X.abs) / float(state.width)
		y = float(state.Y.abs) / float(state.height)

		mouseover_id = None
		if not self.starmap.show_icon:
			mouseover_id = self.starmap.queryObjects(x, y)
		else:
			elements = self.starmap.queryIcons(x, y)
			if len(elements) > 0:
				mouseover_id = self.getIDFromIcon(elements[0])

		if not mouseover_id:
			self.mouseover = None
			self.information_overlay.close()
		elif self.mouseover != mouseover_id:
			self.mouseover = mouseover_id
			self.mouseover_timer.reset()

		return False

	def mouseReleased(self, evt, id):
		#print self, "mouseReleased"

		if self.timeout:
			print "timeout - mouse release not processed"
			return False

		focus = False

		if id == ois.MB_Left:
			if self.singleclick:
				if self.doubleclick_timer.getMilliseconds() < self.doubleclick_timeout:
					focus = True
				self.singleclick = False
			else:
				self.doubleclick_timer.reset()
				self.singleclick = True

		state = evt.get_state()
		if self.mouse_delta[0] <= self.tolerance_delta and self.mouse_delta[1] <= self.tolerance_delta:
			# The mouse hasn't moved much check if the person is clicking on something.
			x = float(state.X.abs) / float(state.width)
			y = float(state.Y.abs) / float(state.height)

			icon = self.starmap.isIconClicked(x, y)
			if icon:
				if id == ois.MB_Left:
					oid = self.getIDFromIcon(icon)
					self.selectObjectById(oid, focus)
					return False

			mouseover_id = self.starmap.queryObjects(x, y)
			if mouseover_id:
				if id == ois.MB_Left:
					selected = self.selectObjectById(mouseover_id, focus)

				if id == ois.MB_Right:
					if self.current_object:
						current_id = self.getIDFromMovable(self.current_object)
						self.moveTo(current_id, mouseover_id)
			return False

	def getCache(self):
		return self.parent.application.cache

	def selectEntity(self, movable):
		"""Highlights and selects the given Entity"""

		id = self.getIDFromMovable(movable)
		#print "SelectObject", id

		if id != None:
			self.selectObjectById(id)

	def selectObjectById(self, id, focus=False):
		"""Selects the object given by id. Returns True if selected."""
		try:
			entity = self.sceneManager.getEntity("Object%i" % id)
		except ogre.OgreItemIdentityException:
			return False

		self.unselect()
		self.current_object = entity

		scale_factor = 25
		if self.objects[id].subtype == PLANET:
			scale_factor = 10
		elif self.objects[id].subtype == FLEET:
			scale_factor = 10
		self.starmap.selectObject(id, scale_factor=scale_factor)

		object = self.objects[id]
		self.info_window.setText(object)

		if focus:
			self.focus(id=id)

		return self.orders_window.updateOrdersWindow(id, self.getCache())

	def unselect(self, evt=None):
		"""Unselect the current object, if any"""
		if self.current_object:
			self.starmap.clearSelection()
			self.current_object = None
			self.orders_menu.close()
			self.orders_window.hideArguments()

	def openOrdersMenu(self):
		"""Open the radial menu which shows available orders"""
		if not self.current_object:
			return

		id = self.getIDFromMovable(self.current_object)
		object = self.objects[id]
		order_types = objectutils.getOrderTypes(self.getCache(), id)
		if len(order_types) > 0:
			self.orders_menu.entity = self.current_object
			if self.orders_menu.toggle():
				descs = OrderDescs()
				for order_type in order_types.popitem()[1]:
					if not descs.has_key(order_type):
						continue
					description = descs[order_type]
					#print description
					self.orders_menu.add(description._name, self.orders_window, "showOrder")
			else:
				self.orders_window.hideArguments()

	def focus(self, evt=None, id=None):
		"""Center and zoom in on the given object"""
		if id is None:
			if self.current_object:
				id = self.getIDFromMovable(self.current_object)
			else:
				return
		self.starmap.center(id)
		target = self.sceneManager.getSceneNode("CameraTarget")
		position = target.position
		position.z = 1000
		target.setPosition(position)
		self.sceneManager.getSceneNode("CameraNode").setPosition(position)
		self.starmap.updateZoom()

	def sendOrder(self, id, order, action="create after", node=None):
		"""Sends an order to the server.

		If node is None, append the order to the end of the queue.

		"""
		cache = self.getCache()
		network = self.parent.application.network
		queue = objectutils.getOrderQueueList(cache, id)
		if not node:
			node = cache.orders[queue[0][1]].last
		evt = cache.apply("orders", action, queue[0][1], node, order)
		self.parent.application.Post(evt, source=self)

	def keyPressed(self, evt):
		if evt.key == ois.KC_A:
			self.starmap.autofit()
		elif evt.key == ois.KC_C:
			if self.current_object:
				self.starmap.center(self.getIDFromMovable(self.current_object))
		elif evt.key == ois.KC_M:
			helpers.toggleWindow("Messages")
		elif evt.key == ois.KC_O:
			helpers.toggleWindow("Orders")
		elif evt.key == ois.KC_S:
			helpers.toggleWindow("System")
		elif evt.key == ois.KC_I:
			helpers.toggleWindow("Information")
		elif evt.key == ois.KC_SPACE:
			wm = cegui.WindowManager.getSingleton()
			self.openOrdersMenu()
		elif evt.key == ois.KC_F11:
			cache = self.getCache()
			helpers.pickle_dump(cache.objects, "object")
			helpers.pickle_dump(cache.designs, "design")
			helpers.pickle_dump(cache.messages, "message")
			helpers.pickle_dump(cache.players, "player")
			helpers.pickle_dump(cache.resources, "resource")
			print "cache dumped"
		elif evt.key == ois.KC_ESCAPE:
			self.toggleMainMenu()

	def keyDown(self, keyboard):
		if keyboard.isKeyDown(ois.KC_LEFT):
			self.starmap.pan(-self.scroll_speed, 0)
		if keyboard.isKeyDown(ois.KC_RIGHT):
			self.starmap.pan(self.scroll_speed, 0)
		if keyboard.isKeyDown(ois.KC_UP):
			self.starmap.pan(0, self.scroll_speed)
		if keyboard.isKeyDown(ois.KC_DOWN):
			self.starmap.pan(0, -self.scroll_speed)
		if keyboard.isKeyDown(ois.KC_EQUALS):
			self.starmap.zoom(-self.scroll_speed)
		if keyboard.isKeyDown(ois.KC_MINUS):
			self.starmap.zoom(self.scroll_speed)

	def moveTo(self, source, destination):
		"""Orders a fleet to move to a destination

		source - ID of the fleet to move
		destination - ID of the destination object

		"""
		object = self.objects[source]
		if object.subtype is FLEET:
			target = self.objects[destination]
			descs = OrderDescs()
			order_types = objectutils.getOrderTypes(self.getCache(), source)
			for order_type in order_types.popitem()[1]:
				if not descs.has_key(order_type):
					continue
				descclass = descs[order_type]
				if descclass._name in ['Move', 'Move To', 'Intercept']:
					orderargs = [0, source, -1, descclass.subtype, 0, []]
					for prop in descclass.properties:
						if isinstance(prop, parameters.OrderParamAbsSpaceCoords):
							pos = [x for x in tp_helpers.getAbsPosition(target)]
							orderargs.append([pos])
						if isinstance(prop, parameters.OrderParamObject):
							orderargs.append(destination)
					order = objects.Order(*orderargs)
					order._dirty = True
					self.sendOrder(source, order)
					self.starmap.connectObjects(source, destination)
					break

	def returnToMain(self):
		"""Return to the login screen"""
		self.clearAll()
		self.created = False
		self.parent.application.network.connection.disconnect()
		self.parent.changeScene(self.parent.login)

	def toggleMainMenu(self, evt=None):
		if not cegui.WindowManager.getSingleton().isWindowPresent("MenuRoot"):
			self.main_menu = gui.MenuWindow(self, self.system)
		else:
			self.main_menu.destroy()

	def clearGui(self):
		"""Empty out all GUI textboxes and hide all windows"""
		for win in self.sub_windows:
			win.clear()
			win.hide()
		self.orders_menu.close()

	def clearAll(self):
		"""Clears the entire starmap scene"""
		self.starmap.clearLines()
		self.starmap.clearOverlays()
		self.starmap.clearObjects()
		self.clearGui()
		self.current_object = None

	def getIDFromMovable(self, movable):
		"""Returns the object id from an Entity node"""
		return long(movable.getName()[6:])

	def getIDFromIcon(self, icon):
		return int(icon.name.split('_')[2])

