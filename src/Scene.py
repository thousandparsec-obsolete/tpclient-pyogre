import math

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui
import ogre.io.OIS as ois

from tp.netlib.objects import OrderDescs
from tp.netlib.objects.constants import *

import overlay
import starmap
import helpers

UNIVERSE = 1
STAR = 2
PLANET = 3
FLEET = 4

class Scene(object):
	"""Displays a scene for the user.

	Can be swapped with other scenes using the show and hide methods.

	"""

	def __init__(self, parent, sceneManager):
		self.parent = parent
		self.guiSystem = parent.guiSystem
		self.sceneManager = sceneManager
		
		# Create the root for this Scene
		self.rootNode = sceneManager.rootSceneNode.createChildSceneNode((0, 0, 0))
		self.camera = self.sceneManager.getCamera( 'PlayerCam' )
		
		# Where to store any GUI windows
		self.windows = []
	
	def show(self):
		"""Called when this SceneManager is being displayed"""
		# Attach the root node
		self.sceneManager.rootSceneNode.addChild(self.rootNode)
	
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
		self.sceneManager.rootSceneNode.removeChild(self.rootNode)

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
		camera = self.sceneManager.getCamera( 'PlayerCam' )
		camera.pitch(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame*25)))
		camera.yaw(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame*-5)))

		return True

class LoginScene(MenuScene):
	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		wm = cegui.WindowManager.getSingleton()

		# when populating a cegui list, must keep the references, otherwise segfault
		self.servers = []

		login = wm.loadWindowLayout("login.layout")
		self.guiSystem.getGUISheet().addChildWindow(login)
		self.windows.append(login)

		helpers.bindEvent("Login/LoginButton", self, "onConnect", cegui.PushButton.EventClicked)
		helpers.bindEvent("Login/ConfigButton", self, "onConfig", cegui.PushButton.EventClicked)
		helpers.bindEvent("Login/QuitButton", self, "onQuit", cegui.PushButton.EventClicked)

		self.hide()

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

	def onConnect(self, evt):
		"""Called when user clicks on the login button"""
		wm = cegui.WindowManager.getSingleton()
		
		host = wm.getWindow("Login/Server").getText().c_str()
		username = wm.getWindow("Login/Username").getText().c_str()
		password = wm.getWindow("Login/Password").getText().c_str()
		
		print "onConnect", host, username, password
		self.parent.application.network.Call( \
				self.parent.application.network.ConnectTo, host, username, password, True)

	def onConfig(self, evt):
		"""Called when user clicks on the config button"""
		print "onConfig"
		wm = cegui.WindowManager.getSingleton()

	def onQuit(self, evt):
		"""Called when user clicks on the quit button"""
		print "onQuit"
		self.parent.Cleanup()

	def setServer(self, host):
		"""Sets the initial value of the host input field"""
		helpers.setWidgetText("Login/Server", host)

class ConfigScene(MenuScene):
	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)
		self.hide()

class StarmapScene(MenuScene):
	"""Manages the GUI and Starmap class"""

	SELECTABLE = 2**1
	UNSELECTABLE = 2**2

	pan_speed = 500
	tolerance_delta = 1
	distance_scale = 900000
	scroll_speed = 100
	max_zoom = -10
	min_zoom = 10

	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		self.mouse_delta = ogre.Vector2(0, 0)
		self.current_object = None
		self.messages = []
		self.message_index = 0
		self.created = False
		self.starmap = starmap.Starmap(self, self.sceneManager, self.rootNode)
	
		self.raySceneQuery = self.sceneManager.createRayQuery(ogre.Ray())
		self.raySceneQuery.setSortByDistance(True, 10)
		self.raySceneQuery.setQueryMask(self.SELECTABLE & ~self.UNSELECTABLE)

		# Load all the billboards
		#self.flareBillboardSets = []
		#for i in xrange(1, 12):
			#billboardSet = self.sceneManager.createBillboardSet("flare%i" % i)
			#billboardSet.setMaterialName("Billboards/Flares/flare%i" % i)
			#billboardSet.setCullIndividually(True)
			#billboardSet.setDefaultDimensions(20, 20)
			#billboardSet.setQueryFlags(self.UNSELECTABLE)
			
			#self.rootNode.attachObject(billboardSet)
			#self.flareBillboardSets.append(billboardSet)

		wm = cegui.WindowManager.getSingleton()
		system = wm.loadWindowLayout("system.layout")
		self.guiSystem.getGUISheet().addChildWindow(system)
		self.windows.append(system)

		helpers.bindEvent("Windows/Information", self, "windowToggle", cegui.PushButton.EventClicked)
		helpers.bindEvent("Windows/Orders", self, "windowToggle", cegui.PushButton.EventClicked)
		helpers.bindEvent("Windows/Messages", self, "windowToggle", cegui.PushButton.EventClicked)
		helpers.bindEvent("Windows/System", self, "windowToggle", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Next", self, "nextMessage", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Prev", self, "prevMessage", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Delete", self, "deleteMessage", cegui.PushButton.EventClicked)
		helpers.bindEvent("System/SystemList", self, "systemSelected", cegui.Listbox.EventSelectionChanged)
		for window in ['Messages', 'Orders', 'System', 'Information']:
			helpers.bindEvent(window, self, "closeClicked", cegui.FrameWindow.EventCloseClicked)

		self.hide()
	
	def show(self):
		Scene.show(self)

	def create(self, cache):
		"""Creates list of objects from cache"""
		print "creating the starmap"
		self.objects = cache.objects
		self.system_list = []

		self.starmap.createBackground()

		wm = cegui.WindowManager.getSingleton()
		listbox = wm.getWindow("System/SystemList")

		for object in self.objects.values():
			pos = ogre.Vector3(
					object.pos[0] / self.distance_scale, 
					object.pos[1] / self.distance_scale, 
					object.pos[2] / self.distance_scale)

			print "creating", object.id, object.name, object._subtype, "at", pos
			
			if object._subtype is STAR:
				node = self.starmap.addStar(object, pos)

				# Add to system list
				item = cegui.ListboxTextItem(object.name)
				item.setSelectionBrushImage("SleekSpace", "ClientBrush")
				item.setSelectionColours(cegui.colour(0.9, 0.9, 0.9))
				item.setAutoDeleted(False)
				self.system_list.append(item)
				listbox.addItem(item)

			if object._subtype is PLANET:
				# Get parent system and the number of other planets
				parent = self.updateObjectIndex(object, "planets", PLANET)
				node = self.starmap.addPlanet(object, pos, parent)

			if object._subtype is FLEET:
				# Get parent system and the number of other fleets
				parent = self.updateObjectIndex(object, "fleets", FLEET)
				node = self.starmap.addFleet(object, pos, parent)

		for val in cache.messages[0]:
			self.messages.append(val)

		if len(self.messages) > 0:
			if len(self.messages) > self.message_index:
				self.setCurrentMessage(self.messages[self.message_index])
			else:
				self.setCurrentMessage(self.messages[0])

		self.created = True

		self.starmap.autofit()

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

	def recreate(self, cache):
		"""Update locations of objects
		
		Assumes stars and planet locations do not change.

		"""
		print "Updating starmap"
		self.objects = cache.objects
		self.starmap.clearLines()

		for object in cache.objects.values():
			pos = ogre.Vector3(
					object.pos[0] / self.distance_scale, 
					object.pos[1] / self.distance_scale, 
					object.pos[2] / self.distance_scale)

			print "updating", object.id, object.name, object._subtype, "at", pos

			if object._subtype is FLEET:
				# Get parent system and the number of other fleets
				# FIXME: What if a fleet is destroyed
				parent = self.updateObjectIndex(object, "fleets", FLEET)
				self.starmap.setFleet(object, pos, parent)

	def update(self, evt):
		return self.starmap.update()

	def onNetworkTimeRemaining(self, evt):
		"""Called whenever a NetworkTimeRemaining packet is received"""
		print "onNetworkRemaining"
		print evt.remaining
		if evt.remaining == 0:
			print "End of turn"
			network = self.parent.application.network
			network.Call(network.CacheUpdate)

	def onNetworkFailure(self, evt):
		"""Called whenever a NetworkFailure packet is received"""
		print "onNetworkFailure"

	def onCacheUpdate(self, evt):
		"""Called whever the cache is updated"""
		print "onCacheUpdate"
		if evt.what is None:
			if self.created:
				self.recreate(self.parent.application.cache)
			else:
				self.create(self.parent.application.cache)

	def mousePressed(self, evt, id):
		print self, "mousePressed"
		self.mouse_delta -= self.mouse_delta
	
	def mouseMoved(self, evt):
		"""Handles the MouseMoved event

		If the middle mouse button is down pan the screen.
		Scrolling the mousewheel will zoom in and out.

		"""
		state = evt.get_state()

		self.mouse_delta += (abs(state.X.rel), abs(state.Y.rel))

		if state.buttonDown(ois.MB_Middle):
			if self.starmap.zoom != 0:
				adjusted_pan = abs(self.pan_speed / (self.starmap.zoom * 2))
			else:
				adjusted_pan = self.pan_speed
			self.camera.moveRelative(
				ogre.Vector3(state.X.rel * adjusted_pan, -state.Y.rel * adjusted_pan, 0))
		
		elif state.Z.rel < 0 and self.starmap.zoom > self.max_zoom: # scroll down
			self.camera.moveRelative(ogre.Vector3(0, 0, 2 * self.pan_speed))
			self.starmap.zoom -= 1

		elif state.Z.rel > 0 and self.starmap.zoom < self.min_zoom: # scroll up
			self.camera.moveRelative(ogre.Vector3(0, 0, -2 * self.pan_speed))
			self.starmap.zoom += 1

		else:
			x = float(state.X.abs) / float(state.width)
			y = float(state.Y.abs) / float(state.height)
			mouseRay = self.camera.getCameraToViewportRay( x, y )
			self.raySceneQuery.setRay(mouseRay)
			for o in self.raySceneQuery.execute():
				if o.movable:
					self.mouseover = o.movable
					break
		
		return False

	def mouseReleased(self, evt, id):
		print self, "mouseReleased"

		state = evt.get_state()
		if self.mouse_delta[0] <= self.tolerance_delta and self.mouse_delta[1] <= self.tolerance_delta:
			# The mouse hasn't moved much check if the person is clicking on something.
			x = float(state.X.abs) / float(state.width)
			y = float(state.Y.abs) / float(state.height)
			mouseRay = self.camera.getCameraToViewportRay(x, y)
			self.raySceneQuery.setRay(mouseRay)

			print "Executing ray scene query"

			for o in self.raySceneQuery.execute():
				if o.worldFragment:
					print "WorldFragment:", o.worldFragment.singleIntersection

				if o.movable:
					# Check there is actually a collision
					print o.movable.getWorldBoundingSphere()
					if not mouseRay.intersects(o.movable.getWorldBoundingSphere()):
						print "False Collision with MovableObject: ", o.movable.getName()
						continue
			
					# We are clicking on something!
					found = True
					oid = self.getIDFromMovable(o.movable)
					
					if id == ois.MB_Left:
						print "MovableObject: ", o.movable.getName()
						return self.selectEntity(o.movable)

					if id == ois.MB_Right:
						if self.current_object:
							current_id = self.getIDFromMovable(self.current_object)
							self.moveTo(current_id, oid)

			return False
	
	def selectEntity(self, movable):
		"""Highlights and selects the given Entity"""

		id = self.getIDFromMovable(movable)
		print "SelectObject", id

		if id != None:
			# Unselect the current object
			if self.current_object:
				self.starmap.clearSelection()
				self.current_object = None

			self.current_object = movable
			scale_factor = 3
			if self.objects[id].subtype == FLEET:
				scale_factor = 25
			self.starmap.selectObject(id, scale_factor=scale_factor)

			object = self.objects[id]
			self.setInformationText(object)

			if object.order_number > 0 or len(object.order_types) > 0:
				wm = cegui.WindowManager.getSingleton()
				order_list = wm.getWindow("Orders/OrderList")
				self.orders = {}
				order_list.resetList()
				descs = OrderDescs()
				for order_type in object.order_types:
					if not descs.has_key(order_type):
						continue
					description = descs[order_type]
					item = cegui.ListboxTextItem(description._name)
					item.setAutoDeleted(False)
					self.orders[item] = order_type
					order_list.addItem(item)

	def keyPressed(self, evt):
		if evt.key == ois.KC_A:
			self.starmap.autofit()
		elif evt.key == ois.KC_C:
			if self.current_object:
				self.starmap.center(self.getIDFromMovable(self.current_object))
		elif evt.key == ois.KC_ESCAPE:
			self.clearAll()
			self.created = False
			self.parent.application.network.connection.disconnect()
			self.parent.changeScene(self.parent.login)

	def keyDown(self, keyboard):
		if keyboard.isKeyDown(ois.KC_LEFT):
			self.camera.moveRelative(ogre.Vector3(-self.scroll_speed, 0, 0))
		if keyboard.isKeyDown(ois.KC_RIGHT):
			self.camera.moveRelative(ogre.Vector3(self.scroll_speed, 0, 0))
		if keyboard.isKeyDown(ois.KC_UP):
			self.camera.moveRelative(ogre.Vector3(0, self.scroll_speed, 0))
		if keyboard.isKeyDown(ois.KC_DOWN):
			self.camera.moveRelative(ogre.Vector3(0, -self.scroll_speed, 0))
		if keyboard.isKeyDown(ois.KC_EQUALS):
			self.camera.moveRelative(ogre.Vector3(0, 0, -self.scroll_speed))
		if keyboard.isKeyDown(ois.KC_MINUS):
			self.camera.moveRelative(ogre.Vector3(0, 0, self.scroll_speed))

	def moveTo(self, source, destination):
		"""Orders a fleet to move to a destination

		source - ID of the fleet to move
		destination - ID of the destination object

		"""
		object = self.objects[source]
		if object.subtype is FLEET:
			target = self.objects[destination]
			descs = OrderDescs()
			for order_type in object.order_types:
				if not descs.has_key(order_type):
					continue
				descclass = descs[order_type]
				if descclass._name in ['Move', 'Move To', 'Intercept']:
					orderargs = [0, source, -1, descclass.subtype, 0, []]
					for name, t in descclass.names:
						if t is ARG_ABS_COORD:
							orderargs.append(target.pos)
					order = descclass(*orderargs)

					cache = self.parent.application.cache
					network = self.parent.application.network
					node = cache.orders[source].first
					evt = cache.apply("orders", "create after", source, node, order)
					network.Call(network.OnCacheDirty, evt)

					self.starmap.drawLine(source, destination)
					break

	def nextMessage(self, evt):
		"""Sets messagebox to the next message if available"""
		if len(self.messages) > 0 and self.message_index < len(self.messages) - 1:
			self.message_index += 1
			self.setCurrentMessage(self.messages[self.message_index])

	def prevMessage(self, evt):
		"""Sets messagebox to the previous message if available"""
		if len(self.messages) > 0 and self.message_index > 0:
			self.message_index -= 1
			self.setCurrentMessage(self.messages[self.message_index])

	def deleteMessage(self, evt):
		"""Deletes the current message permanently and displays the next message, if any."""
		cache = self.parent.application.cache
		network = self.parent.application.network
		current_message = self.messages[self.message_index]
		change_node = cache.messages[0][current_message.id]
		evt = cache.apply("messages", "remove", 0, change_node, None)
		network.Call(network.OnCacheDirty, evt)
		self.messages.remove(current_message)
		if len(self.messages) > 0:
			self.nextMessage(evt)
		else:
			helpers.setWidgetText("Messages/Message", "")

	def setCurrentMessage(self, message_object):
		"""Sets message text inside message window"""
		message = message_object.CurrentOrder
		text = "Subject: " + message.subject + "\n"
		text += "\n"
		text += message.body
		helpers.setWidgetText("Messages/Message", text)

	def setInformationText(self, object):
		"""Sets text inside information window"""
		text = "modify time: " + object.modify_time.ctime() + "\n"
		text += "name: " + object.name + "\n"
		text += "parent: " + str(object.parent) + "\n"
		text += "position: " + str(object.pos) + "\n"
		text += "velocity: " + str(object.vel) + "\n"
		text += "id: " + str(object.id) + "\n"
		text += "size: " + str(object.size) + "\n"
		helpers.setWidgetText("Information/Text", text)

	def systemSelected(self, evt):
		"""Updates information box with selected system info"""
		print "System selected"
		wm = cegui.WindowManager.getSingleton()
		listbox = wm.getWindow("System/SystemList")
		selected = listbox.getFirstSelectedItem()
		for obj in self.objects.values():
			if obj.name == selected.text:
				self.setInformationText(obj)
				break

	def closeClicked(self, evt):
		"""Called when user clicks on the close button of a window"""
		evt.window.setVisible(not evt.window.isVisible())

	def windowToggle(self, evt):
		"""Toggles visibility of a window"""
		wm = cegui.WindowManager.getSingleton()
		# assume buttons and windows have the same name, minus prefix
		name = evt.window.getName().c_str().split("/")[1]
		if name != None:
			window = wm.getWindow(name)
			window.setVisible(not window.isVisible())

	def clearGui(self):
		"""Empty out all GUI textboxes and hide all windows"""
		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("Orders/OrderList").resetList()
		wm.getWindow("System/SystemList").resetList()
		wm.getWindow("Messages/Message").setText("")
		wm.getWindow("Information/Text").setText("")
		for window in ['Orders', 'System', 'Messages', 'Information']:
			wm.getWindow(window).hide()
	
	def clearAll(self):
		"""Clears the entire starmap scene"""
		self.starmap.clearLines()
		self.starmap.clearOverlays()
		self.starmap.clearObjects()
		self.clearGui()

	def getIDFromMovable(self, movable):
		"""Returns the object id from an Entity node"""
		return long(movable.getName()[6:])

