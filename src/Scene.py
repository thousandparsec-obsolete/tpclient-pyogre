import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui
import ogre.io.OIS as ois

def setWidgetText(name, text):
	wm = cegui.WindowManager.getSingleton()
	wm.getWindow(name).setText(text)

def bindButtonEvent(name, object, method):
	wm = cegui.WindowManager.getSingleton()
	wm.getWindow(name).subscribeEvent(cegui.PushButton.EventClicked, object, method)

class Scene:
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
		"""
		Called when this SceneManager is being displayed.
		"""
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
		"""
		Called when this SceneManager is no longer being displayed.
		"""
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

class MenuScene(Scene):
	"""
	Menu Scenes all share a common background. The state of the 
	background is preserved accross Menu Scenes.
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

	def keyPressed(self, evt):
		if evt.key == ois.KC_A:
			
			print "A!"

class LoginScene(MenuScene):
	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		wm = cegui.WindowManager.getSingleton()

		# when populating a cegui list, must keep the references, otherwise segfault
		self.servers = []

		login = wm.loadWindowLayout("login.layout")
		self.guiSystem.getGUISheet().addChildWindow(login)
		self.windows.append(login)

		bindButtonEvent("Login/LoginButton", self, "onConnect")
		bindButtonEvent("Login/ConfigButton", self, "onConfig")
		bindButtonEvent("Login/QuitButton", self, "onQuit")

		self.hide()

	def onFoundRemoteGame(self, evt):
		print "found remote game"
		location = evt.game.locations["tp"][0][0]
		print location
		wm = cegui.WindowManager.getSingleton()
		combobox = wm.getWindow("Login/Server")
		item = cegui.ListboxTextItem(location)
		self.servers.append(item)
		combobox.addItem(item)

	def onConnect(self, evt):
		wm = cegui.WindowManager.getSingleton()
		
		host = wm.getWindow("Login/Server").getText().c_str()
		username = wm.getWindow("Login/Username").getText().c_str()
		password = wm.getWindow("Login/Password").getText().c_str()
		#host = "demo2.thousandparsec.net"
		#host = "localhost"
		#username = "test"
		#password = "12345"
		
		print "onConnect", host, username, password
		self.parent.application.network.Call( \
				self.parent.application.network.ConnectTo, host, username, password, True)

	def onConfig(self, evt):
		print "onConfig"
		wm = cegui.WindowManager.getSingleton()

	def onQuit(self, evt):
		print "onQuit"
		self.parent.Cleanup()

	def setServer(self, host):
		setWidgetText("Login/Server", host)

class ConfigScene(MenuScene):
	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		#login = cegui.WindowManager.getSingleton().loadWindowLayout("config.layout")
		#self.guiSystem.guiSheet.addChildWindow(login)
		#self.windows.append(login)

		self.hide()

class ObjectOverlay:
	def __init__(self, node, object):
		self.node = node
		self.entity = "Object%i" % object.id
		self.active = []

		overlayManager = ogre.OverlayManager.getSingleton()
		panel = overlayManager.createOverlayElement("Panel", "Panel%i" % object.id)
		panel.metricsMode = ogre.GMM_PIXELS
		# FIXME: This should be calculated...
		panel.dimensions = (100, 100)
		self.panel = panel
	
		name = overlayManager.createOverlayElement("TextArea", "Name%i" % object.id)
		name.metricsMode = ogre.GMM_PIXELS
		name.charHeight = 16
		name.fontName = "Tahoma-12"
		name.caption = object.name
		self.name = name

		#position = overlayManager.createOverlayElement("TextArea", "Position%i" % object.id)
		#position.metricsMode = ogre.GMM_PIXELS
		#position.setPosition(0, 16)
		#position.charHeight = 16
		#position.fontName = "Tahoma-12"
		#position.caption = "%i, %i, %i" % object.pos
		#self.position = position

		self.overlay = overlayManager.create("Overlay%i" % object.id)
		self.overlay.add2D(self.panel)

		# WARN: This needs to happen after the panel is added to an overlay
		panel.addChild(name)
		#panel.addChild(position)

	def show(self, *which):
		for text in self.active:
			text.hide()

		self.active = which

		for text in self.active:
			text.show()

	def update(self, camera):
		entity = self.node.getAttachedObject(0)
	
		pos = self.node.worldPosition
		pos = camera.viewMatrix*pos
		pos = camera.projectionMatrix*pos
	
		if abs(pos[0]) < 1 and abs(pos[1]) < 1 and pos[2] < 1 and entity.visible:
			if not self.overlay.isVisible():
				self.overlay.show()

			pos /= 2

			pos = ((0.5 + pos.x)*camera.viewport.actualWidth, (0.5 - pos.y)*camera.viewport.actualHeight)
			self.panel.setPosition(pos[0], pos[1])
		else:
			if self.overlay.isVisible():
				self.overlay.hide()

	def setColour(self, ColourValue):
		for overlay in (self.name, self.position):
			overlay.colour = ColourValue
	def getColour(self):
		return self.name.ColourValue
	colour = property(getColour, setColour)

class StarmapScene(MenuScene):
	SELECTABLE = 2**1
	UNSELECTABLE = 2**2

	panSpeed = 500
	rotateSpeed = 5
	toleranceDelta = 0.001

	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		ogre.FontManager.getSingleton().load("Tahoma-12","General")

		self.mouseDelta = ogre.Vector2(0, 0)
		self.currentObject = None
	
		self.raySceneQuery = self.sceneManager.createRayQuery( ogre.Ray() )
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

		self.nodes = {}
		self.overlays = {}

		wm = cegui.WindowManager.getSingleton()

		system = wm.loadWindowLayout("system.layout")
		self.guiSystem.getGUISheet().addChildWindow(system)
		self.windows.append(system)

		# Bind gui events
		bindButtonEvent("Windows/Information", self, "onWindowToggle")
		bindButtonEvent("Windows/Orders", self, "onWindowToggle")
		bindButtonEvent("Windows/Messages", self, "onWindowToggle")
		bindButtonEvent("Windows/System", self, "onWindowToggle")

		self.hide()
	
	def onWindowToggle(self, evt):
		wm = cegui.WindowManager.getSingleton()
		# assume buttons and windows have the same name, minus prefix
		name = evt.window.getName().c_str().split("/")[1]
		if name != None:
			window = wm.getWindow(name)
			window.setVisible(not window.isVisible())

	def onNetworkRemaining(self, evt):
		print "onNetworkRemaining"

	def onCacheUpdate(self, evt):
		print "onCacheUpdate"
		if evt.what is None:
			self.create(self.parent.application.cache)
	
	def create(self, cache):
		print "creating the starmap"
		self.objects = cache.objects
		self.nodes = {}
		self.overlays = {}

		for object in self.objects.values():
			#pos = ogre.Vector3(*object.pos)
			scale = 900000
			pos = ogre.Vector3(object.pos[0]/scale, object.pos[1]/scale, object.pos[2]/scale)
			print object._subtype
			print "creating", object.id, object.name, "at", pos
			
			if object._subtype is 2:
				node = self.rootNode.createChildSceneNode(pos)
				self.nodes[object.id] = node

				# Selectable entity
				entityNode = node.createChildSceneNode(ogre.Vector3(0, 0, 0))
				entity = self.sceneManager.createEntity("Object%i" % object.id, 'sphere.mesh')
				entity.queryFlags = self.SELECTABLE
				scale = 50/entity.mesh.boundingSphereRadius
				entityNode.setScale(ogre.Vector3(scale,scale,scale))
				entityNode.attachObject(entity)
		
				# Lens flare
				billboardSet = self.flareBillboardSets[object.id % len(self.flareBillboardSets)]
				billboard = billboardSet.createBillboard(pos, ogre.ColourValue.White)
		
				# Text overlays
				overlay = ObjectOverlay(entityNode, object)
				overlay.show(overlay.name)
				self.overlays[object.id] = overlay

		#self.autofit()
	
	def autofit(self):
		fit = False
		self.camera.setPosition(ogre.Vector3(0,0,0))
		while not fit:
			self.camera.moveRelative(ogre.Vector3(0, 0, 500))

			fit = True
			for key in self.nodes:
				object = self.nodes[key]
				if not self.camera.isVisible(object.getPosition()):
					fit = False

	def update(self, evt):
		camera = self.sceneManager.getCamera( 'PlayerCam' )
		for overlay in self.overlays.values():
			overlay.update(camera)
		return True

	def mousePressed(self, evt, id):
		print self, "mousePressed"
		self.mouseDelta -= self.mouseDelta

		#self.mouseState = evt.get_state().buttons
		#if id & ogre.MouseEvent.BUTTON0_MASK:
			#self.mouseState |= ogre.MouseEvent.BUTTON0_MASK
		
		#if id & ogre.MouseEvent.BUTTON2_MASK:
			#self.mouseState |= ogre.MouseEvent.BUTTON2_MASK
	
		#print id, self.mouseState
	
	def mouseMoved(self, evt):
		"""
		If the right mouse is down roll/pitch for camera changes.
		If the left mouse button is down pan the screen
		"""
		state = evt.get_state()

		self.mouseDelta += (abs(state.X.rel), abs(state.Y.rel))
		#if self.mouseDelta.length > self.toleranceDelta:
			#cegui.MouseCursor.getSingleton().hide()

		if state.buttonDown(ois.MB_Right):
			# This won't introduce roll as setFixedYawAxis is True
			#self.camera.yaw(ogre.Radian(ogre.Degree(-state.X.rel * self.rotateSpeed)))
			#self.camera.pitch(ogre.Radian(ogre.Degree(-state.Y.rel * self.rotateSpeed)))
			self.camera.moveRelative(
				ogre.Vector3(state.X.rel * self.panSpeed, -state.Y.rel * self.panSpeed, 0))
		
		elif state.buttonDown(ois.MB_Left):
			self.camera.moveRelative(
				ogre.Vector3(state.X.rel * self.panSpeed, 0, state.Y.rel * self.panSpeed))

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
		#print id & self.mouseState
		#self.mouseState = evt.get_state().buttons
		#if id & ogre.MouseEvent.BUTTON0_MASK:
			#self.mouseState &= ~ogre.MouseEvent.BUTTON0_MASK
		
		#if id & ogre.MouseEvent.BUTTON2_MASK:
			#self.mouseState &= ~ogre.MouseEvent.BUTTON2_MASK

		#if evt.get_state().buttons == 0:
			#cegui.MouseCursor.getSingleton().show()

		state = evt.get_state()
		#if self.mouseDelta.length < self.toleranceDelta:
		if True:
			# Unselect the current object
			if self.currentObject:
				self.currentObject.getParentSceneNode().showBoundingBox(False)
				self.currentObject = None

			# The mouse hasn't moved much check if the person is clicking on something.
			x = float(state.X.abs) / float(state.width)
			y = float(state.Y.abs) / float(state.height)
			print "%d, %d" % (state.width, state.height)
			print "%f, %f" % (state.X.abs, state.Y.abs)
			print "coord: ", x, y
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
					
					print "MovableObject: ", o.movable.getName()
					self.currentObject = o.movable
					self.currentObject.getParentSceneNode().showBoundingBox(True)

					# Call the
					return self.mouseSelectObject(long(o.movable.getName()[6:]))
			return self.mouseSelectObject(None)
	
	def mouseSelectObject(self, id):
		print "SelectObject", id
		pass

	def keyPressed(self, evt):
		if evt.key == ois.KC_A:
			self.autofit()

	def mode(self, modes):
		if self.OWNERS in modes:
			for id, object in self.objects.items():
				if object.owner in (0, -1):
					self.overlays[id].colour = ogre.ColorValue.Blue
				else:
					self.overlays[id].colour = ogre.ColorValue.Yellow
		
