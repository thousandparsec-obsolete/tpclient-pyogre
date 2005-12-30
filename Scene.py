from pyogre import cegui, ogre, ogreaddons

class Scene:
	def __init__(self, application, sceneManager):
		self.application = application
		self.guiSystem = application.guiSystem
		self.sceneManager = sceneManager
		
		# Create the root for this Scene
		self.rootNode = sceneManager.rootSceneNode.createChildSceneNode((0, 0, 0))
		
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
	
	def hide(self):
		"""
		Called when this SceneManager is no longer being displayed.
		"""
		# Save camera position and orientation
		camera = self.sceneManager.getCamera( 'PlayerCam' )
		self.position = camera.position
		self.orientation = camera.orientation

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
	def __init__(self, application, sceneManager):
		Scene.__init__(self, application, sceneManager)

		#entity = sceneManager.createEntity('LoginRobot', 'Testing')
		#entity.setMaterialName("Core/OgreText");
		#self.rootNode.createChildSceneNode((15, 15, 0)).attachObject(entity)
	
		login = cegui.WindowManager.getSingleton().loadWindowLayout("login.layout")
		self.guiSystem.guiSheet.addChildWindow(login)
		self.windows.append(login)

		self.hide()

class ConfigScene(MenuScene):
	def __init__(self, application, sceneManager):
		Scene.__init__(self, application, sceneManager)

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
		name.caption = str(object.id)
		self.name = name

		position = overlayManager.createOverlayElement("TextArea", "Position%i" % object.id)
		position.metricsMode = ogre.GMM_PIXELS
		position.setPosition(0, 16)
		position.charHeight = 16
		position.fontName = "Tahoma-12"
		position.caption = "%i, %i, %i" % (object.posx, object.posy, object.posz)
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
		
		if abs(pos[0]) < 1 and abs(pos[1]) < 1 and entity.visible:
			if not self.overlay.isVisible():
				self.overlay.show()

			pos /= 2

			pos = ((0.5 + pos.x)*camera.viewport.actualWidth, (0.5 - pos.y)*camera.viewport.actualHeight)
			self.panel.setPosition(pos[0], pos[1])
		else:
			if self.overlay.isVisible():
				self.overlay.hide()

class StarmapScene(MenuScene):
	SELECTABLE = 2**1
	UNSELECTABLE = 2**2

	panSpeed = 5000
	rotateSpeed = 250

	def __init__(self, application, sceneManager):
		Scene.__init__(self, application, sceneManager)

		ogre.FontManager.getSingleton().load("Tahoma-12","General")

		self.mouseState = 0
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

		# Quick-selection
		#system = cegui.WindowManager.getSingleton().loadWindowLayout("system.layout")
		#self.guiSystem.guiSheet.addChildWindow(system)
		#self.windows.append(system)

		class o:
			def __init__(self, id, x, y, z):
				self.id = id
				self.posx = x
				self.posy = y
				self.posz = z

		class cache:
			pass

		c= cache()
		c.objects = {0: o(0, 0, 1000, 0), 1: o(1, -100, -100, 100), 2:o(2, 100, 100, 100),
			4: o(4, 0, 1123, 0), 5: o(5,-1132, -1123, 1232), 6:o(6, 1136, 8990, 2300),
			7: o(7, 0, 5623, 0), 8: o(8, -1532, -1683, 1267), 9:o(9, 2223, 8990, 0000),
			10: o(10, 0, 1134, 0), 11: o(11, -1832, -1233, 1232), 12:o(12, 1136, 8000, 2300),
			13: o(13, 0, 1222, 0), 14: o(14, -2322, -1193, 1289), 15:o(15,1178, 8990, 2000),
		}

		self.create(c)
		self.hide()
	
	def create(self, cache):
		self.nodes = {}
		self.overlays = {}

		for object in cache.objects.values():
			pos = ogre.Vector3(object.posx, object.posy, object.posz)
			
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

		# Is the person clicking on something?
		mouseRay = self.sceneManager.getCamera( 'PlayerCam' ).getCameraToViewportRay( evt.x, evt.y )
		self.raySceneQuery.ray = mouseRay
		result = self.raySceneQuery.execute()

		print result

		for o in result:
			if o.worldFragment:
				print "WorldFragment:", o.worldFragment.singleIntersection

			if o.movable:
				if isinstance(o.movable, ogre.BillboardSet):
					print "Got a BillboardSet!?"
					continue
			
				# Check there is actually a collision
				print o.movable.worldBoundingSphere
				if not mouseRay.intersects(o.movable.worldBoundingSphere):
					print "False Collision with MovableObject: ", o.movable.name, o.movable.mesh.name
					continue
			
				print "MovableObject: ", o.movable.name, o.movable.mesh.name
				if self.currentObject:
					self.currentObject.parentSceneNode.showBoundingBox = False
				self.currentObject = o.movable
				self.currentObject.parentSceneNode.showBoundingBox = True
				break
		
		if evt.buttonID & ogre.MouseEvent.BUTTON0_MASK:
			self.mouseState |= ogre.MouseEvent.BUTTON0_MASK
		
		if evt.buttonID & ogre.MouseEvent.BUTTON2_MASK:
			self.mouseState |= ogre.MouseEvent.BUTTON2_MASK
	
		print evt.buttonID, self.mouseState
	
		if self.mouseState != 0:
			cegui.MouseCursor.getSingleton().hide()
	
	def mouseDragged(self, evt):
		"""
		If the right mouse is down roll/pitch for camera changes.
		If the left mouse button is down pan the screen
		"""
		camera = self.sceneManager.getCamera( 'PlayerCam' )

		if self.mouseState & ogre.MouseEvent.BUTTON2_MASK:
			# This won't introduce roll as setFixedYawAxis is True
			camera.yaw(ogre.Radian(ogre.Degree(-evt.relX * self.rotateSpeed)))
			camera.pitch(ogre.Radian(ogre.Degree(-evt.relY * self.rotateSpeed)))
		
		if self.mouseState & ogre.MouseEvent.BUTTON0_MASK:
			camera.moveRelative(
				ogre.Vector3(evt.relX * self.panSpeed, 0, -evt.relY * self.panSpeed))
		
		return False

	def mouseReleased(self, evt):
		print self, "mouseReleased"
		if evt.buttonID & ogre.MouseEvent.BUTTON0_MASK:
			self.mouseState &= ~ogre.MouseEvent.BUTTON0_MASK
		
		if evt.buttonID & ogre.MouseEvent.BUTTON2_MASK:
			self.mouseState &= ~ogre.MouseEvent.BUTTON2_MASK

		if self.mouseState == 0:
			cegui.MouseCursor.getSingleton().show()

		return False
