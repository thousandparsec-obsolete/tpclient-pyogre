import math

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui
import ogre.io.OIS as ois

from tp.netlib.objects import OrderDescs
from tp.netlib.objects.constants import *

import overlay
import starmap
import helpers
import gui

UNIVERSE = 1
STAR = 2
PLANET = 3
FLEET = 4

OBJECT = 1

defaults = {
	ARG_ABS_COORD: [0,0,0],
	ARG_TIME: [0, 0],
	ARG_OBJECT: [0],
	ARG_PLAYER: [0,0],
	ARG_STRING: [0, ""],
	ARG_LIST: [[], []],
	ARG_RANGE: [-1, -1, -1, -1],
}

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
		camera = self.sceneManager.getCamera('PlayerCam')
		camera.pitch(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame * 2)))
		camera.yaw(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame * -2)))

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

	SELECTABLE = 1 << 0
	UNSELECTABLE = 1 << 1

	pan_speed = 500
	tolerance_delta = 1
	distance_scale = 500000
	scroll_speed = 100
	max_zoom_out = -5
	min_zoom_in = 19

	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		self.mouse_delta = ogre.Vector2(0, 0)
		self.current_object = None
		self.messages = []
		self.message_index = 0
		self.goto_index = 0
		self.created = False
		self.starmap = starmap.Starmap(self, self.sceneManager, self.rootNode)
		self.timeout = False

		self.camera_node = self.rootNode.createChildSceneNode("CameraNode")
		self.camera_node.attachObject(self.camera)

		# FIXME: Shift to starmap
		self.raySceneQuery = self.sceneManager.createRayQuery(ogre.Ray())
		self.raySceneQuery.setSortByDistance(True, 10)
		self.raySceneQuery.setQueryMask(self.SELECTABLE)
		self.camera.setQueryFlags(self.UNSELECTABLE)

		wm = cegui.WindowManager.getSingleton()
		system = wm.loadWindowLayout("system.layout")
		self.guiSystem.getGUISheet().addChildWindow(system)
		self.windows.append(system)

		helpers.bindEvent("Windows/Information", self, "windowToggle", cegui.PushButton.EventClicked)
		helpers.bindEvent("Windows/Orders", self, "windowToggle", cegui.PushButton.EventClicked)
		helpers.bindEvent("Windows/Messages", self, "windowToggle", cegui.PushButton.EventClicked)
		helpers.bindEvent("Windows/System", self, "windowToggle", cegui.PushButton.EventClicked)
		helpers.bindEvent("System/SystemList", self, "systemSelected", cegui.Listbox.EventSelectionChanged)
		for window in ['Messages', 'Orders', 'System', 'Information']:
			helpers.bindEvent(window, self, "closeClicked", cegui.FrameWindow.EventCloseClicked)

		self.message_window = gui.MessageWindow(self)
		self.arguments_window = gui.ArgumentsWindow(self)

		order_queue = wm.getWindow("Orders/OrderQueue")
		order_queue.addColumn("Type", 0, cegui.UDim(0.4, 0))
		order_queue.addColumn("Turns left", 1, cegui.UDim(0.4, 0))
		order_queue.setSelectionMode(cegui.MultiColumnList.RowSingle)

		self.orders_menu = overlay.RadialMenu(self.camera)
		wm.getWindow("Starmap").addChildWindow(self.orders_menu.menu)

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

		designs = self.getDesigns(cache)

		for object in self.objects.values():
			pos = ogre.Vector3(
					object.pos[0] / self.distance_scale, 
					object.pos[1] / self.distance_scale, 
					object.pos[2] / self.distance_scale)

			print "creating", object.id, object.name, "\ttype:", object._subtype, "at", pos

			if hasattr(object, "parent"):
				print "parent of %s is %i" % (object.name, object.parent)
			
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
				if object.parent != 1 and self.starmap.hasObject(object.parent):
					pos = self.starmap.nodes[object.parent].position
				node = self.starmap.addPlanet(object, pos, parent)

			if object._subtype is FLEET:
				# Get parent system and the number of other fleets
				parent = self.updateObjectIndex(object, "fleets", FLEET)
				# Assign fleet type according to how many designs player has
				fleet_type = (object.ships[0][0] - 1) % designs[object.owner]
				print "ship_design: %i designs: %i fleet type: %i" % (object.ships[0][0], designs[object.owner], fleet_type)
				if object.parent != 1 and self.starmap.hasObject(object.parent):
					pos = self.starmap.nodes[object.parent].position
				node = self.starmap.addFleet(object, pos, parent, fleet_type, self.SELECTABLE)

		self.message_window.create(cache)
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
		self.starmap.clearLines()
		designs = self.getDesigns(cache)

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
				if object.parent != 1 and self.starmap.hasObject(object.parent):
					pos = self.starmap.nodes[object.parent].position

				if self.starmap.hasObject(object.id):
					self.starmap.setFleet(object, pos, parent)
				else:
					fleet_type = (object.ships[0][0] - 1) % designs[object.owner]
					self.starmap.addFleet(object, pos, parent, fleet_type)

	def update(self, evt):
		return self.starmap.update()

	def onNetworkTimeRemaining(self, evt):
		"""Called whenever a NetworkTimeRemaining packet is received"""
		print "onNetworkRemaining"
		print evt.remaining
		if evt.remaining == 0:
			print "End of turn"
			self.timeout = True
			network = self.parent.application.network
			network.Call(network.CacheUpdate)

	def onNetworkFailure(self, evt):
		"""Called whenever a NetworkFailure packet is received"""
		print "onNetworkFailure"

	def onCacheUpdate(self, evt):
		"""Called whever the cache is updated"""
		print "onCacheUpdate", evt
		cache = self.parent.application.cache
		if self.created:
			if self.timeout:
				self.recreate(cache)
				self.timeout = False
			elif self.current_object:
				self.arguments_window.update()
		else:
			self.create(cache)

	def onCacheDirty(self, evt):
		print "OnCacheDirty", evt

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
			#self.camera_node.translate(
				#ogre.Vector3(state.X.rel * adjusted_pan, -state.Y.rel * adjusted_pan, 0))
		
		elif state.Z.rel < 0 and self.starmap.zoom > self.max_zoom_out: # scroll down
			#self.camera.moveRelative(ogre.Vector3(0, 0, 2 * self.pan_speed))
			self.camera_node.translate(ogre.Vector3(0, 0, 2 * self.pan_speed))
			self.starmap.zoom -= 1

		elif state.Z.rel > 0 and self.starmap.zoom < self.min_zoom_in: # scroll up
			#self.camera.moveRelative(ogre.Vector3(0, 0, -2 * self.pan_speed))
			self.camera_node.translate(ogre.Vector3(0, 0, -2 * self.pan_speed))
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
		#print self, "mouseReleased"

		state = evt.get_state()
		if self.mouse_delta[0] <= self.tolerance_delta and self.mouse_delta[1] <= self.tolerance_delta:
			# The mouse hasn't moved much check if the person is clicking on something.
			x = float(state.X.abs) / float(state.width)
			y = float(state.Y.abs) / float(state.height)
			mouseRay = self.camera.getCameraToViewportRay(x, y)

			icon = self.starmap.isIconClicked(x, y)
			if icon:
				if id == ois.MB_Left:
					name = icon.name
					oid = int(name.split('_')[2])
					self.selectObjectById(oid)
					return False

			# FIXME: Shift to starmap
			self.raySceneQuery.setRay(mouseRay)

			#print "Executing ray scene query", x, y

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
			self.selectObjectById(id)

	def selectObjectById(self, id):
		"""Selects the object given by id. Returns True if selected."""
		try:
			entity = self.sceneManager.getEntity("Object%i" % id)
		except ogre.OgreItemIdentityException:
			return False

		# Unselect the current object
		if self.current_object:
			self.starmap.clearSelection()
			self.current_object = None
			self.orders_menu.close()
			self.arguments_window.hide()

		self.current_object = entity

		scale_factor = 25
		if self.objects[id].subtype == PLANET:
			scale_factor = 10
		elif self.objects[id].subtype == FLEET:
			scale_factor = 10
		self.starmap.selectObject(id, scale_factor=scale_factor)

		object = self.objects[id]
		self.setInformationText(object)

		wm = cegui.WindowManager.getSingleton()
		order_queue = wm.getWindow("Orders/OrderQueue")
		order_list = wm.getWindow("Orders/OrderList")
		order_queue.resetList()
		order_list.resetList()

		self.order_queue_items = []

		if not hasattr(self.parent, "application"):
			return True

		for o_node in self.parent.application.cache.orders[id]:
			index = order_queue.addRow()
			order = o_node.CurrentOrder
			item = cegui.ListboxTextItem(order._name)
			item.setAutoDeleted(False)
			item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
			self.order_queue_items.append(item)
			order_queue.setItem(item, 0, index) # col id, row id

			item = cegui.ListboxTextItem(str(order.turns))
			item.setAutoDeleted(False)
			order_queue.setItem(item, 1, index)
			self.order_queue_items.append(item)

		if object.order_number > 0 or len(object.order_types) > 0:
			self.orders = {}
			descs = OrderDescs()
			for order_type in object.order_types:
				if not descs.has_key(order_type):
					continue
				description = descs[order_type]
				item = cegui.ListboxTextItem(description._name)
				item.setAutoDeleted(False)
				self.orders[item] = order_type
				order_list.addItem(item)

		return True

	def openOrdersMenu(self):
		if not self.current_object:
			return

		id = self.getIDFromMovable(self.current_object)
		object = self.objects[id]
		if object.order_number > 0 or len(object.order_types) > 0:
			self.orders_menu.entity = self.current_object
			if self.orders_menu.toggle():
				descs = OrderDescs()
				for order_type in object.order_types:
					if not descs.has_key(order_type):
						continue
					description = descs[order_type]
					print description
					self.orders_menu.add(description._name, self, "showOrder")
			else:
				self.arguments_window.hide()

	def showOrder(self, evt):
		index = int(evt.window.name.c_str()[17:])
		id = self.getIDFromMovable(self.current_object)
		object = self.objects[id]
		descs = OrderDescs()
		orders = []
		for order_type in object.order_types:
			if not descs.has_key(order_type):
				continue
			orders.append(descs[order_type])
		order_description = orders[index]

		self.arguments = []
		orderargs = [0, id, -1, order_description.subtype, 0, []]
		for name, t in order_description.names:
			#print name, ARG_NAMEMAP[t]
			orderargs += defaults[t]

		order = order_description(*orderargs)

		self.sendOrder(id, order)

		for name, t in order_description.names:
			self.arguments_window.addArgument(name, t)

		self.arguments_window.show(order_description._name)
		self.arguments_window.setCurrentOrder(id, order_description.subtype)

		# remember to close after an order

	def sendOrder(self, id, order, action="create after"):
		cache = self.parent.application.cache
		network = self.parent.application.network
		node = cache.orders[id].first
		evt = cache.apply("orders", action, id, node, order)
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
			cache = self.parent.application.cache
			helpers.pickle_dump(cache.objects, "object")
			helpers.pickle_dump(cache.designs, "design")
			helpers.pickle_dump(cache.messages, "message")
			print "cache dumped"
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
		if keyboard.isKeyDown(ois.KC_HOME):
			self.camera.pitch(ogre.Radian(0.03))
		if keyboard.isKeyDown(ois.KC_END):
			self.camera.pitch(ogre.Radian(-0.03))
		if keyboard.isKeyDown(ois.KC_DELETE):
			self.camera.yaw(ogre.Radian(-0.03))
		if keyboard.isKeyDown(ois.KC_PGDOWN):
			self.camera.yaw(ogre.Radian(0.03))

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
						if t is ARG_OBJECT:
							orderargs.append(destination)
					order = descclass(*orderargs)
					self.sendOrder(source, order)
					self.starmap.drawLine(source, destination)
					break

	def setInformationText(self, object):
		"""Sets text inside information window"""
		# FIXME: Create information window class
		text = "modify time: " + object.modify_time.ctime() + "\n"
		text += "name: " + object.name + "\n"
		text += "parent: " + str(object.parent) + "\n"
		text += "position: " + str(object.pos) + "\n"
		text += "velocity: " + str(object.vel) + "\n"
		text += "id: " + str(object.id) + "\n"
		text += "size: " + str(object.size) + "\n"
		if hasattr(object, "owner"):
			text += "owner: " + str(object.owner) + "\n"
		if hasattr(object, "ships"):
			text += "ships: " + str(object.ships) + "\n"
		helpers.setWidgetText("Information/Text", text)

	def systemSelected(self, evt):
		"""Updates information box with selected system info"""
		print "System selected"
		# FIXME: Create system window class
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
			helpers.toggleWindow(name)

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

