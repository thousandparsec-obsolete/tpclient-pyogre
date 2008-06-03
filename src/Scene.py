import math

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui
import ogre.io.OIS as ois

from tp.netlib.objects import OrderDescs, Order
from tp.netlib.objects.constants import *
from tp.client.threads import NetworkThread

import overlay

UNIVERSE = 1
STAR = 2
PLANET = 3
FLEET = 4

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

		bindEvent("Login/LoginButton", self, "onConnect", cegui.PushButton.EventClicked)
		bindEvent("Login/ConfigButton", self, "onConfig", cegui.PushButton.EventClicked)
		bindEvent("Login/QuitButton", self, "onQuit", cegui.PushButton.EventClicked)

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
		setWidgetText("Login/Server", host)

class ConfigScene(MenuScene):
	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)
		self.hide()

class StarmapScene(MenuScene):
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
		self.nodes = {}
		self.overlays = {}
		self.messages = []
		self.message_index = 0
		self.lines = 0
		self.created = False
		self.zoom = 0
		self.bg_particle = None
	
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

		bindEvent("Windows/Information", self, "windowToggle", cegui.PushButton.EventClicked)
		bindEvent("Windows/Orders", self, "windowToggle", cegui.PushButton.EventClicked)
		bindEvent("Windows/Messages", self, "windowToggle", cegui.PushButton.EventClicked)
		bindEvent("Windows/System", self, "windowToggle", cegui.PushButton.EventClicked)
		bindEvent("Messages/Next", self, "nextMessage", cegui.PushButton.EventClicked)
		bindEvent("Messages/Prev", self, "prevMessage", cegui.PushButton.EventClicked)
		bindEvent("Messages/Delete", self, "deleteMessage", cegui.PushButton.EventClicked)
		bindEvent("System/SystemList", self, "systemSelected", cegui.Listbox.EventSelectionChanged)
		for window in ['Messages', 'Orders', 'System', 'Information']:
			bindEvent(window, self, "closeClicked", cegui.FrameWindow.EventCloseClicked)

		self.hide()
	
	def show(self):
		Scene.show(self)

	def createBackground(self):
		"""Creates a starry background for the current scene"""
		if self.bg_particle is None:
			self.bg_particle = self.sceneManager.createParticleSystem("stars", "Space/Stars")
		particleNode = self.rootNode.createChildSceneNode("StarryBackground")
		particleNode.pitch(ogre.Radian(1.57))
		particleNode.attachObject(self.bg_particle)

	def create(self, cache):
		"""Creates list of objects from cache"""
		print "creating the starmap"
		self.objects = cache.objects
		self.system_list = []

		self.createBackground()

		wm = cegui.WindowManager.getSingleton()
		listbox = wm.getWindow("System/SystemList")

		for object in self.objects.values():
			pos = ogre.Vector3(
					object.pos[0] / self.distance_scale, 
					object.pos[1] / self.distance_scale, 
					object.pos[2] / self.distance_scale)

			print "creating", object.id, object.name, object._subtype, "at", pos
			
			if object._subtype is STAR:
				node = self.createObjectNode(pos, object.id, 'sphere.mesh', 100)
				self.nodes[object.id] = node
				entityNode = self.sceneManager.getSceneNode("Object%i_EntityNode" % object.id)

				# Lens flare
				#billboardSet = self.flareBillboardSets[object.id % len(self.flareBillboardSets)]
				#billboard = billboardSet.createBillboard(pos, ogre.ColourValue.White)
		
				# Text overlays
				label = overlay.ObjectOverlay(entityNode, object)
				label.show(label.name)
				label.setColour(ogre.ColourValue(0.7, 0.9, 0.7))
				self.overlays[object.id] = label

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

				pos = self.calculateRadialPosition(pos, 100, 720, parent.planets, object.index)

				node = self.createObjectNode(pos, object.id, 'sphere.mesh', 50)
				self.nodes[object.id] = node
				entity = self.sceneManager.getEntity("Object%i" % object.id)
				entity.setMaterialName("Starmap/Planet")

			if object._subtype is FLEET:
				# Get parent system and the number of other fleets
				parent = self.updateObjectIndex(object, "fleets", FLEET)
				pos = self.calculateRadialPosition(pos, 200, 360, parent.fleets, object.index)

				node = self.createObjectNode(pos, object.id, 'ship.mesh', 50)
				self.nodes[object.id] = node
				entityNode = node.getChild(0)
				entityNode.yaw(ogre.Radian(1.57))
				entityNode.roll(ogre.Radian(1.57))

		for val in cache.messages[0]:
			self.messages.append(val)

		if len(self.messages) > 0:
			if len(self.messages) > self.message_index:
				self.setCurrentMessage(self.messages[self.message_index])
			else:
				self.setCurrentMessage(self.messages[0])

		self.created = True

		self.autofit()

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

	def calculateRadialPosition(self, position, radius, total_degree, total_objects, object_index):
		"""Updates the position of an object orbiting around it's parent

		position - The current position of the object
		radius - The distance from the parent
		total_degree - How many total degrees there are
		total_objects - How many objects in total surrounding the parent
		object_index - Index of the current object
		
		"""
		interval = (total_degree / total_objects) * object_index
		x = radius * math.cos(interval)
		y = radius * math.sin(interval)
		position.x += x
		position.y += y
		return position

	def createObjectNode(self, pos, oid, mesh, scale):
		"""Returns a scene node containing the scaled entity mesh
		
		pos - The current position of the object
		oid - The ID of the object
		mesh - String containing the mesh file name
		scale - How much to scale the object by

		"""
		node = self.rootNode.createChildSceneNode("Object%i_Node" % oid, pos)
		entityNode = node.createChildSceneNode("Object%i_EntityNode" % oid, ogre.Vector3(0, 0, 0))
		entity = self.sceneManager.createEntity("Object%i" % oid, mesh)
		entity.queryFlags = self.SELECTABLE
		obj_scale = scale / entity.mesh.boundingSphereRadius
		entityNode.setScale(ogre.Vector3(obj_scale, obj_scale, obj_scale))
		entityNode.attachObject(entity)
		return node

	def recreate(self, cache):
		"""Update locations of objects
		
		Assumes stars and planet locations do not change.

		"""
		print "Updating starmap"
		self.objects = cache.objects
		self.clearLines()

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

				pos = self.calculateRadialPosition(pos, 200, 360, parent.fleets, object.index)

				node = self.nodes[object.id]
				node.setPosition(pos)

	def update(self, evt):
		camera = self.sceneManager.getCamera( 'PlayerCam' )
		for label in self.overlays.values():
			label.update(camera)
		return True

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
			if self.zoom != 0:
				adjusted_pan = abs(self.pan_speed / (self.zoom * 2))
			else:
				adjusted_pan = self.pan_speed
			self.camera.moveRelative(
				ogre.Vector3(state.X.rel * adjusted_pan, -state.Y.rel * adjusted_pan, 0))
		
		elif state.Z.rel < 0 and self.zoom > self.max_zoom: # scroll down
			self.camera.moveRelative(ogre.Vector3(0, 0, 2 * self.pan_speed))
			self.zoom -= 1

		elif state.Z.rel > 0 and self.zoom < self.min_zoom: # scroll up
			self.camera.moveRelative(ogre.Vector3(0, 0, -2 * self.pan_speed))
			self.zoom += 1

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
				self.current_object.getParentSceneNode().showBoundingBox(False)
				self.current_object = None

			self.current_object = movable
			self.current_object.getParentSceneNode().showBoundingBox(True)

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
			self.autofit()
		elif evt.key == ois.KC_C:
			if self.current_object:
				self.center(self.getIDFromMovable(self.current_object))
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

					self.drawLine(source, destination)
					break

	def mode(self, modes):
		if self.OWNERS in modes:
			for id, object in self.objects.items():
				if object.owner in (0, -1):
					self.overlays[id].colour = ogre.ColorValue.Blue
				else:
					self.overlays[id].colour = ogre.ColorValue.Yellow
		
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
			setWidgetText("Messages/Message", "")

	def setCurrentMessage(self, message_object):
		"""Sets message text inside message window"""
		message = message_object.CurrentOrder
		text = "Subject: " + message.subject + "\n"
		text += "\n"
		text += message.body
		setWidgetText("Messages/Message", text)

	def setInformationText(self, object):
		"""Sets text inside information window"""
		text = "modify time: " + object.modify_time.ctime() + "\n"
		text += "name: " + object.name + "\n"
		text += "parent: " + str(object.parent) + "\n"
		text += "position: " + str(object.pos) + "\n"
		text += "velocity: " + str(object.vel) + "\n"
		text += "id: " + str(object.id) + "\n"
		text += "size: " + str(object.size) + "\n"
		setWidgetText("Information/Text", text)

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

	def drawLine(self, id_start, id_end):
		"""Draws a line showing the path of an object.

		id_start - ID of the moving object
		id_end - ID of the object's destination

		"""
		start_node = self.nodes[id_start]
		end_node = self.nodes[id_end]
		manual_object = self.sceneManager.createManualObject("line%i" % self.lines)
		scene_node = self.rootNode.createChildSceneNode("line%i_node" % self.lines)

		material = ogre.MaterialManager.getSingleton().create("line%i_material" % self.lines, "default")
		material.setReceiveShadows(False)
		material.getTechnique(0).getPass(0).setAmbient(0,1,0)

		manual_object.begin("line%i_material" % self.lines, ogre.RenderOperation.OT_LINE_LIST)
		manual_object.position(start_node.position)
		manual_object.position(end_node.position)
		manual_object.end()

		scene_node.attachObject(manual_object)
		self.lines += 1

	def clearLines(self):
		"""Removes all lines created by the drawLine method"""
		for i in range(self.lines):
			self.sceneManager.destroySceneNode("line%i_node" % i)
			self.sceneManager.destroyEntity("line%i" % i)
			ogre.MaterialManager.getSingleton().remove("line%i_material" % i)
		self.lines = 0

	def clearOverlays(self):
		"""Clears all the object labels"""
		for ov in self.overlays.values():
			ov.destroy()
		self.overlays = {}

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
		self.clearLines()
		self.clearOverlays()
		self.clearGui()
		self.sceneManager.destroyAllEntities()
		self.rootNode.removeAndDestroyAllChildren()

	def getIDFromMovable(self, movable):
		"""Returns the object id from an Entity node"""
		return long(movable.getName()[6:])

	def autofit(self):
		"""Zooms out until all stars are visible"""
		fit = False
		self.camera.setPosition(ogre.Vector3(0,0,0))
		while not fit:
			self.camera.moveRelative(ogre.Vector3(0, 0, 500))

			fit = True
			for key in self.nodes:
				object = self.nodes[key]
				if not self.camera.isVisible(object.getPosition()):
					fit = False
		self.zoom = 0

	def center(self, id):
		"""Center on an object identified by object id"""
		node = self.nodes[id]
		pos = node.getPosition()
		cam = self.camera.getPosition()
		self.camera.setPosition(ogre.Vector3(pos.x,pos.y,cam.z))

