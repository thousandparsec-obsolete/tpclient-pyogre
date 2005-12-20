from pyogre import cegui, ogre

import Mesh

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
		camera.pitch(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame*25)))
		camera.yaw(ogre.Radian(ogre.Degree(evt.timeSinceLastFrame*-5)))

class LoginScene(MenuScene):
	def __init__(self, sceneManager, guiSystem):
		Scene.__init__(self, sceneManager)

		#Mesh.createSphere('Testing', 10)

		#entity = sceneManager.createEntity('LoginRobot', 'Testing')
		#entity.setMaterialName("Core/OgreText");
		#self.rootNode.createChildSceneNode((15, 15, 0)).attachObject(entity)
	
		login = cegui.WindowManager.getSingleton().loadWindowLayout("login.layout")
		guiSystem.guiSheet.addChildWindow(login)
		self.windows.append(login)

		self.hide()

class ConfigScene(MenuScene):
	def __init__(self, sceneManager, guiSystem):
		Scene.__init__(self, sceneManager)

		#login = cegui.WindowManager.getSingleton().loadWindowLayout("config.layout")
		#guiSystem.guiSheet.addChildWindow(login)
		#self.windows.append(login)

		self.hide()

class StarmapScene(MenuScene):
	def __init__(self, sceneManager, guiSystem):
		Scene.__init__(self, sceneManager)

		# Quick-selection
		#system = cegui.WindowManager.getSingleton().loadWindowLayout("system.layout")
		#guiSystem.guiSheet.addChildWindow(system)
		#self.windows.append(system)

		class o:
			def __init__(self, x, y, z):
				self.posx = x
				self.posy = y
				self.posz = z

		class cache:
			pass

		c= cache()
		c.objects = {0: o(0, 1000, 0), 1: o(-1000, -1000, 1000), 2:o(1000, 1000, 1000),
			4: o(0, 1123, 0), 5: o(-1132, -1123, 1232), 6:o(1136, 8990, 2300),
			4: o(0, 5623, 0), 5: o(-1532, -1683, 1267), 6:o(2223, 8990, 0000),
			4: o(0, 1134, 0), 5: o(-1832, -1233, 1232), 6:o(1136, 8000, 2300),
			4: o(0, 1222, 0), 5: o(-2322, -1193, 1289), 6:o(1178, 8990, 2000),
		}


		self.create(c)

		self.hide()
	
	def create(self, cache):
		systems = self.sceneManager.createBillboardSet("Systems", len(cache.objects.keys()));
		systems.cullIndividually = True
		systems.defaultDimensions = (1,1)

		self.rootNode.createChildSceneNode((0, 0, 0)).attachObject(systems)

		for object in cache.objects.values():
			object_board = systems.createBillboard((object.posx, object.posy, object.posz))
			object_board.colour = ogre.ColourValue.White


		
