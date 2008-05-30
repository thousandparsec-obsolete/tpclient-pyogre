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

	panSpeed = 500
	rotateSpeed = 5
	toleranceDelta = 1
	distance_scale = 900000
	scrollSpeed = 100

	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		self.mouseDelta = ogre.Vector2(0, 0)
		self.currentObject = None
		self.nodes = {}
		self.overlays = {}
		self.messages = []
		self.message_index = 0
		self.created = False
	
		self.raySceneQuery = self.sceneManager.createRayQuery(ogre.Ray())
		self.raySceneQuery.setSortByDistance(True, 10)
		self.raySceneQuery.setQueryMask(self.SELECTABLE & ~self.UNSELECTABLE)

		# Load all the billboards
		self.flareBillboardSets = []
		for i in xrange(1, 12):
			billboardSet = self.sceneManager.createBillboardSet("flare%i" % i)
			billboardSet.setMaterialName("Billboards/Flares/flare%i" % i)
			billboardSet.setCullIndividually(True)
			billboardSet.setDefaultDimensions(20, 20)
			billboardSet.setQueryFlags(self.UNSELECTABLE)
			
			self.rootNode.attachObject(billboardSet)
			self.flareBillboardSets.append(billboardSet)

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
		bindEvent("System/SystemList", self, "systemSelected", cegui.Listbox.EventSelectionChanged)
		for window in ['Messages', 'Orders', 'System', 'Information']:
			bindEvent(window, self, "closeClicked", cegui.FrameWindow.EventCloseClicked)

		self.hide()
	
	def create(self, cache):
		"""Creates list of objects from cache"""
		print "creating the starmap"
		self.objects = cache.objects
		self.system_list = []

		wm = cegui.WindowManager.getSingleton()
		listbox = wm.getWindow("System/SystemList")

		for object in self.objects.values():
			pos = ogre.Vector3(
					object.pos[0]/self.distance_scale, 
					object.pos[1]/self.distance_scale, 
					object.pos[2]/self.distance_scale)

			print "creating", object.id, object.name, object._subtype, "at", pos
			
			if object._subtype is STAR:
				node = self.rootNode.createChildSceneNode(pos)
				self.nodes[object.id] = node

				# Selectable entity
				entityNode = node.createChildSceneNode(ogre.Vector3(0, 0, 0))
				entity = self.sceneManager.createEntity("Object%i" % object.id, 'sphere.mesh')
				entity.queryFlags = self.SELECTABLE
				obj_scale = 100/entity.mesh.boundingSphereRadius
				entityNode.setScale(ogre.Vector3(obj_scale,obj_scale,obj_scale))
				entityNode.attachObject(entity)
		
				# Lens flare
				billboardSet = self.flareBillboardSets[object.id % len(self.flareBillboardSets)]
				billboard = billboardSet.createBillboard(pos, ogre.ColourValue.White)
		
				# Text overlays
				label = overlay.ObjectOverlay(entityNode, object)
				label.show(label.name)
				label.setColour(ogre.ColourValue(0.7, 0.9, 0.7))
				self.overlays[object.id] = label

				# Add to system list
				item = cegui.ListboxTextItem(object.name)
				item.setSelectionBrushImage("SleekSpace", "ClientBrush")
				item.setSelectionColours(cegui.colour(0.9, 0.9, 0.9))
				self.system_list.append(item)
				listbox.addItem(item)

			if object._subtype is PLANET:
				# Get parent system and the number of other planets
				parent = self.objects[object.parent]
				if not hasattr(parent, "planets"):
					parent.planets = 0
					index = 1
					for i in self.objects.values():
						if i._subtype is 3 and i.parent == object.parent:
							i.index = index
							index += 1
							parent.planets += 1

				radius = 100
				interval = (720 / parent.planets) * object.index
				x = radius * math.cos(interval)
				y = radius * math.sin(interval)
				pos.x += x
				pos.y += y

				node = self.rootNode.createChildSceneNode(pos)
				self.nodes[object.id] = node
				entityNode = node.createChildSceneNode(ogre.Vector3(0, 0, 0))
				entity = self.sceneManager.createEntity("Object%i" % object.id, 'sphere.mesh')
				entity.setMaterialName("Starmap/Planet")
				entity.queryFlags = self.SELECTABLE
				obj_scale = 50/entity.mesh.boundingSphereRadius
				entityNode.setScale(ogre.Vector3(obj_scale,obj_scale,obj_scale))
				entityNode.attachObject(entity)

			if object._subtype is FLEET:
				# Get parent system and the number of other fleets
				parent = self.objects[object.parent]
				if not hasattr(parent, "fleets") or not hasattr(object, "index"):
					parent.fleets = 0
					index = 1
					for i in self.objects.values():
						if i._subtype is FLEET and i.parent == object.parent:
							i.index = index
							index += 1
							parent.fleets += 1

				radius = 200
				interval = (360 / parent.fleets) * object.index
				x = radius * math.cos(interval)
				y = radius * math.sin(interval)
				pos.x += x
				pos.y += y

				node = self.rootNode.createChildSceneNode(pos)
				self.nodes[object.id] = node
				entityNode = node.createChildSceneNode(ogre.Vector3(0, 0, 0))
				entity = self.sceneManager.createEntity("Object%i" % object.id, 'ship.mesh')
				entity.queryFlags = self.SELECTABLE
				obj_scale = 50 / entity.mesh.boundingSphereRadius
				entityNode.setScale(ogre.Vector3(obj_scale,obj_scale,obj_scale))
				entityNode.attachObject(entity)
				entityNode.yaw(ogre.Radian(1.57))
				entityNode.roll(ogre.Radian(1.57))

		for val in cache.messages[0]:
			message = val.CurrentOrder
			self.messages.append(message)

		if len(self.messages) > 0:
			self.setCurrentMessage(self.messages[self.message_index])

		self.created = True

		self.autofit()

	def recreate(self, cache):
		"""Update locations of objects
		
		Assumes stars and planet locations do not change.
		"""
		print "Updating starmap"
		self.objects = cache.objects

		for object in cache.objects.values():
			pos = ogre.Vector3(
					object.pos[0]/self.distance_scale, 
					object.pos[1]/self.distance_scale, 
					object.pos[2]/self.distance_scale)

			print "updating", object.id, object.name, object._subtype, "at", pos

			if object._subtype is FLEET:
				# Get parent system and the number of other fleets
				# FIXME: What if a fleet is destroyed
				parent = self.objects[object.parent]
				if not hasattr(parent, "fleets") or not hasattr(object, "index"):
					parent.fleets = 0
					index = 1
					for i in self.objects.values():
						if i._subtype is FLEET and i.parent == object.parent:
							i.index = index
							index += 1
							parent.fleets += 1

				radius = 200
				interval = (360 / parent.fleets) * object.index
				x = radius * math.cos(interval)
				y = radius * math.sin(interval)
				pos.x += x
				pos.y += y

				node = self.nodes[object.id]
				node.setPosition(pos)

	def setCurrentMessage(self, message):
		"""Sets message text inside message window"""
		wm = cegui.WindowManager.getSingleton()
		msgbox = wm.getWindow("Messages/Message")
		text = "Subject: " + message.subject + "\n"
		text += "\n"
		text += message.body
		msgbox.setText(text)

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

	def center(self, id):
		"""Center on an object identified by object id"""
		node = self.nodes[id]
		pos = node.getPosition()
		cam = self.camera.getPosition()
		self.camera.setPosition(ogre.Vector3(pos.x,pos.x,cam.z))

	def update(self, evt):
		camera = self.sceneManager.getCamera( 'PlayerCam' )
		for label in self.overlays.values():
			label.update(camera)
		return True

	def setInformationText(self, object):
		"""Sets text inside information window"""
		wm = cegui.WindowManager.getSingleton()
		infobox = wm.getWindow("Information/Text")
		text = "modify time: " + object.modify_time.ctime() + "\n"
		text += "name: " + object.name + "\n"
		text += "parent: " + str(object.parent) + "\n"
		text += "position: " + str(object.pos) + "\n"
		text += "velocity: " + str(object.vel) + "\n"
		text += "id: " + str(object.id) + "\n"
		text += "size: " + str(object.size) + "\n"
		infobox.setText(text)

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

	def nextMessage(self, evt):
		"""Sets messagebox to the next message if available"""
		if self.message_index < len(self.messages) - 1:
			self.message_index += 1
			self.setCurrentMessage(self.messages[self.message_index])

	def prevMessage(self, evt):
		"""Sets messagebox to the previous message if available"""
		if self.message_index > 0:
			self.message_index -= 1
			self.setCurrentMessage(self.messages[self.message_index])

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

	def mousePressed(self, evt, id):
		print self, "mousePressed"
		self.mouseDelta -= self.mouseDelta
	
	def mouseMoved(self, evt):
		"""Handles the MouseMoved event

		If the middle mouse button is down pan the screen.
		Scrolling the mousewheel will zoom in and out.

		"""
		state = evt.get_state()

		self.mouseDelta += (abs(state.X.rel), abs(state.Y.rel))
		#if self.mouseDelta.length > self.toleranceDelta:
			#cegui.MouseCursor.getSingleton().hide()

		if state.buttonDown(ois.MB_Middle):
			self.camera.moveRelative(
				ogre.Vector3(state.X.rel * self.panSpeed, -state.Y.rel * self.panSpeed, 0))
		
		elif state.Z.rel < 0:
			self.camera.moveRelative(
				ogre.Vector3(0, 0, 2 * self.panSpeed))

		elif state.Z.rel > 0:
			self.camera.moveRelative(
				ogre.Vector3(0, 0, -2 * self.panSpeed))

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
		if self.mouseDelta[0] <= self.toleranceDelta and self.mouseDelta[1] <= self.toleranceDelta:
			# The mouse hasn't moved much check if the person is clicking on something.
			x = float(state.X.abs) / float(state.width)
			y = float(state.Y.abs) / float(state.height)
			#print "%d, %d" % (state.width, state.height)
			#print "%f, %f" % (state.X.abs, state.Y.abs)
			#print "coord: ", x, y
			mouseRay = self.camera.getCameraToViewportRay( x, y )
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
						# Unselect the current object
						if self.currentObject:
							self.currentObject.getParentSceneNode().showBoundingBox(False)
							self.currentObject = None

						print "MovableObject: ", o.movable.getName()
						self.currentObject = o.movable
						self.currentObject.getParentSceneNode().showBoundingBox(True)

						return self.mouseSelectObject(oid)

					if id == ois.MB_Right:
						if self.currentObject:
							current_id = self.getIDFromMovable(self.currentObject)
							object = self.objects[current_id]
							if object.subtype == 4:
								target = self.objects[oid]
								descs = OrderDescs()
								for order_type in object.order_types:
									if not descs.has_key(order_type):
										continue
									descclass = descs[order_type]
									if descclass._name in ['Move', 'Move To', 'Intercept']:
										orderargs = [0, current_id, -1, descclass.subtype, 0, []]
										for name, t in descclass.names:
											if t is ARG_ABS_COORD:
												orderargs.append(target.pos)
										order = descclass(*orderargs)

										cache = self.parent.application.cache
										network = self.parent.application.network
										node = cache.orders[current_id].first
										evt = cache.apply("orders", "create after", current_id, node, order)
										network.Call(network.OnCacheDirty, evt)
										break

			return self.mouseSelectObject(None)
	
	def getIDFromMovable(self, movable):
		return long(movable.getName()[6:])

	def mouseSelectObject(self, id):
		print "SelectObject", id
		if id != None:
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
		if evt.key == ois.KC_C:
			if self.currentObject:
				id = long(self.currentObject.getName()[6:])
				self.center(id)

	def keyDown(self, keyboard):
		if keyboard.isKeyDown(ois.KC_LEFT):
			self.camera.moveRelative(ogre.Vector3(-self.scrollSpeed, 0, 0))
		if keyboard.isKeyDown(ois.KC_RIGHT):
			self.camera.moveRelative(ogre.Vector3(self.scrollSpeed, 0, 0))
		if keyboard.isKeyDown(ois.KC_UP):
			self.camera.moveRelative(ogre.Vector3(0, self.scrollSpeed, 0))
		if keyboard.isKeyDown(ois.KC_DOWN):
			self.camera.moveRelative(ogre.Vector3(0, -self.scrollSpeed, 0))
		if keyboard.isKeyDown(ois.KC_EQUALS):
			self.camera.moveRelative(ogre.Vector3(0, 0, -self.scrollSpeed))
		if keyboard.isKeyDown(ois.KC_MINUS):
			self.camera.moveRelative(ogre.Vector3(0, 0, self.scrollSpeed))

	def mode(self, modes):
		if self.OWNERS in modes:
			for id, object in self.objects.items():
				if object.owner in (0, -1):
					self.overlays[id].colour = ogre.ColorValue.Blue
				else:
					self.overlays[id].colour = ogre.ColorValue.Yellow
		
