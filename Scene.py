from pyogre import cegui, ogre

class Scene:
	def __init__(self, sceneManager):
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
		pass

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
		camera.pitch(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame*0.25)))
		camera.yaw(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame*-0.5)))

class LoginScene(MenuScene):
	def __init__(self, sceneManager, guiSystem):
		Scene.__init__(self, sceneManager)

		entity = sceneManager.createEntity('LoginRobot', 'robot.mesh')
		self.rootNode.createChildSceneNode((0, 0, 25)).attachObject(entity)
	
		login = cegui.WindowManager.getSingleton().loadWindowLayout("login.layout")
		guiSystem.guiSheet.addChildWindow(login)
		self.windows.append(login)

		camera = sceneManager.getCamera( 'PlayerCam' )
		camera.position = (100, 50, 100)
		camera.lookAt(-50, 50, 0)

		self.hide()

class NinjaScene(MenuScene):
	def __init__(self, sceneManager, guiSystem):
		Scene.__init__(self, sceneManager)

		entity = sceneManager.createEntity('Ninja', 'ninja.mesh')
		self.rootNode.createChildSceneNode((0, 0, 0)).attachObject(entity)

		self.hide()
