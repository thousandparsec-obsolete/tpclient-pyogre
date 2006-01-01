from pyogre import cegui, ogre, ogreaddons

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

		# Dettach the root node
		self.sceneManager.rootSceneNode.removeChild(self.rootNode)

	def update(self, evt):
		return True
	
	# Note, the GUI system always gets fed before the Scene does
	def mouseDragged(self, evt):
		return False

	def mousePressed(self, evt):
		return False

	def mouseReleased(self, evt):
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
		if evt.key == ogre.KC_A:
			
			print "A!"

class LoginScene(MenuScene):
	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		wm = cegui.WindowManager.getSingleton()

		#entity = sceneManager.createEntity('LoginRobot', 'Testing')
		#entity.setMaterialName("Core/OgreText");
		#self.rootNode.createChildSceneNode((15, 15, 0)).attachObject(entity)
	
		login = wm.loadWindowLayout("login.layout")
		self.guiSystem.guiSheet.addChildWindow(login)
		self.windows.append(login)

		loginButton = wm.getWindow("Login/LoginButton")
		configButton = wm.getWindow("Login/ConfigButton")
		quitButton = wm.getWindow("Login/QuitButton")
		
		loginButton.subscribeEvent(loginButton.EventClicked, self.onConnect)
		configButton.subscribeEvent(configButton.EventClicked, self.onConfig)
		quitButton.subscribeEvent(quitButton.EventClicked, self.onQuit)

		self.hide()

	def onConnect(self, evt):
		wm = cegui.WindowManager.getSingleton()
		
		host = wm.getWindow("Login/Server").text
		username = wm.getWindow("Login/Username").text
		password = wm.getWindow("Login/Password").text
		
		print "onConnect", host, username, password
		self.parent.application.network.Call( \
			self.parent.application.network.ConnectTo, host, username, password, True)

	def onConfig(self, evt):
		print "onConfig"

	def onQuit(self, evt):
		print "onQuit"

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

		position = overlayManager.createOverlayElement("TextArea", "Position%i" % object.id)
		position.metricsMode = ogre.GMM_PIXELS
		position.setPosition(0, 16)
		position.charHeight = 16
		position.fontName = "Tahoma-12"
		position.caption = "%i, %i, %i" % object.pos
		self.position = position

		self.overlay = overlayManager.create("Overlay%i" % object.id)
		self.overlay.add2D(self.panel)

		# WARN: This needs to happen after the panel is added to an overlay
		panel.addChild(name)
		panel.addChild(position)

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

	panSpeed = 5000
	rotateSpeed = 250
	toleranceDelta = 0.001

	def __init__(self, parent, sceneManager):
		Scene.__init__(self, parent, sceneManager)

		ogre.FontManager.getSingleton().load("Tahoma-12","General")

		self.mouseState = 0
		self.mouseDelta = ogre.Vector2(0, 0)
		self.currentObject = None
	
		self.raySceneQuery = self.sceneManager.createRayQuery( ogre.Ray() )
		self.raySceneQuery.sortByDistance = True
		self.raySceneQuery.maxResults = 10
		self.raySceneQuery.queryMask = self.SELECTABLE & ~self.UNSELECTABLE

		# Load all the billboards
		self.flareBillboardSets = []
		for i in xrange(1, 12):
			billboardSet = self.sceneManager.createBillboardSet("flare%i" % i)
			billboardSet.materialName = "Billboards/Flares/flare%i" % i
			billboardSet.cullIndividually = True
			billboardSet.defaultDimensions = (20, 20)
			billboardSet.queryFlags = self.UNSELECTABLE
			
			self.rootNode.attachObject(billboardSet)
			self.flareBillboardSets.append(billboardSet)

		self.nodes = {}
		self.overlays = {}

		# Quick-selection
		#system = cegui.WindowManager.getSingleton().loadWindowLayout("system.layout")
		#self.guiSystem.guiSheet.addChildWindow(system)
		#self.windows.append(system)
		self.hide()
	
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
			pos = ogre.Vector3(*object.pos)
			print "creating", object.id, object.name, "at", pos
			
			node = self.rootNode.createChildSceneNode(pos)
			self.nodes[object.id] = node

			# Selectable entity
			entityNode = node.createChildSceneNode(ogre.Vector3(0, 0, 0))
			entity = self.sceneManager.createEntity("Object%i" % object.id, 'sphere.mesh')
			entity.queryFlags = self.SELECTABLE
			scale = 10/entity.mesh.boundingSphereRadius
			entityNode.scale = ogre.Vector3(scale,scale,scale)
			entityNode.attachObject(entity)
	
			# Lense flare
			billboardSet = self.flareBillboardSets[object.id % len(self.flareBillboardSets)]
			billboard = billboardSet.createBillboard(pos, ogre.ColourValue.White)
	
			# Text overlays
			overlay = ObjectOverlay(entityNode, object)
			overlay.show(overlay.name, overlay.position)
			self.overlays[object.id] = overlay

	def update(self, evt):
		camera = self.sceneManager.getCamera( 'PlayerCam' )
		for overlay in self.overlays.values():
			overlay.update(camera)
		return True

	def mousePressed(self, evt):
		print self, "mousePressed"
		self.mouseDelta -= self.mouseDelta

		if evt.buttonID & ogre.MouseEvent.BUTTON0_MASK:
			self.mouseState |= ogre.MouseEvent.BUTTON0_MASK
		
		if evt.buttonID & ogre.MouseEvent.BUTTON2_MASK:
			self.mouseState |= ogre.MouseEvent.BUTTON2_MASK
	
		print evt.buttonID, self.mouseState
	
	def mouseDragged(self, evt):
		"""
		If the right mouse is down roll/pitch for camera changes.
		If the left mouse button is down pan the screen
		"""
		self.mouseDelta += (abs(evt.relX), abs(evt.relY))
		if self.mouseDelta.length > self.toleranceDelta:
			cegui.MouseCursor.getSingleton().hide()
	
		if self.mouseState & ogre.MouseEvent.BUTTON2_MASK:
			# This won't introduce roll as setFixedYawAxis is True
			self.camera.yaw(ogre.Radian(ogre.Degree(-evt.relX * self.rotateSpeed)))
			self.camera.pitch(ogre.Radian(ogre.Degree(-evt.relY * self.rotateSpeed)))
		
		if self.mouseState & ogre.MouseEvent.BUTTON0_MASK:
			self.camera.moveRelative(
				ogre.Vector3(evt.relX * self.panSpeed, 0, evt.relY * self.panSpeed))
		
		return False

	def mouseReleased(self, evt):
		print self, "mouseReleased"
		if evt.buttonID & ogre.MouseEvent.BUTTON0_MASK:
			self.mouseState &= ~ogre.MouseEvent.BUTTON0_MASK
		
		if evt.buttonID & ogre.MouseEvent.BUTTON2_MASK:
			self.mouseState &= ~ogre.MouseEvent.BUTTON2_MASK

		if self.mouseState == 0:
			cegui.MouseCursor.getSingleton().show()

		if self.mouseDelta.length < self.toleranceDelta:
			# Unselect the current object
			if self.currentObject:
				self.currentObject.parentSceneNode.showBoundingBox = False
				self.currentObject = None

			# The mouse hasn't moved much check if the person is clicking on something.
			mouseRay = self.camera.getCameraToViewportRay( evt.x, evt.y )
			self.raySceneQuery.ray = mouseRay

			for o in self.raySceneQuery.execute():
				if o.worldFragment:
					print "WorldFragment:", o.worldFragment.singleIntersection

				if o.movable:
					# Check there is actually a collision
					print o.movable.worldBoundingSphere
					if not mouseRay.intersects(o.movable.worldBoundingSphere):
						print "False Collision with MovableObject: ", o.movable.name, o.movable.mesh.name
						continue
			
					# We are clicking on something!
					found = True
					
					print "MovableObject: ", o.movable.name, o.movable.mesh.name
					self.currentObject = o.movable
					self.currentObject.parentSceneNode.showBoundingBox = True

					# Call the
					return self.mouseSelectObject(long(o.movable.name[6:]))
			return self.mouseSelectObject(None)
	
	def mouseSelectObject(self, id):
		print "SelectObject", id
		pass

	def mode(self, modes):
		if self.OWNERS in modes:
			for id, object in self.objects.items():
				if object.owner in (0, -1):
					self.overlays[id].colour = ogre.ColorValue.Blue
				else:
					self.overlays[id].colour = ogre.ColorValue.Yellow
		
