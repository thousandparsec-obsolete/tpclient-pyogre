import os

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui
import ogre.io.OIS as ois
import ogreal

import console
import settings
from log import *

class Application(object):
	"""This class is the base for an Ogre application"""
	window_title = "Render Window"

	def __init__(self):
		self.frameListener = None
		self.root = None
		self.camera = None
		self.renderWindow = None
		self.sceneManager = None
		self.soundManager = None

	def __del__(self):
		"""Clear variables, this should not actually be needed"""
		del self.camera
		del self.soundManager
		del self.sceneManager
		del self.frameListener
		del self.root
		del self.renderWindow

	def go(self):
		"""Starts the rendering loop"""
		if not self._setUp():
			return
		if self._isPsycoEnabled():
			self._activatePsyco()
		self.root.startRendering()

	def _setUp(self):
		"""This sets up the ogre application

		Returns false if the user hits "cancel" in the dialog box.
		
		"""
		self._createLogger()
		self.root = ogre.Root("plugins.cfg", "ogre.cfg")
		settings.renderers = self.root.getAvailableRenderers()

		self._setUpResources()
		if not self._configure():
			return False
		
		self._chooseSceneManager()
		self._createCamera()
		self._createViewports()

		if settings.sound_support:
			self._createSoundManager()
		else:
			settings.sound_effects = False
			settings.music = False

		ogre.TextureManager.getSingleton().defaultNumMipmaps = 5

		self._createResourceListener()
		self._loadResources()

		self._createScene()
		self._createFrameListener()
		return True

	def _createLogger(self):
		self.logMgr = ogre.LogManager()
		self.logListener = Logger()
		self.log = ogre.LogManager.getSingletonPtr().createLog(
				"dummy.log", 
				True, 
				False, 
				False)
		self.log.addListener(self.logListener)

	def _setUpResources(self):
		"""This sets up Ogre's resources, which are required to be in resources.cfg"""
		config = ogre.ConfigFile()
		config.load('resources.cfg')
		seci = config.getSectionIterator()
		while seci.hasMoreElements():
			secName = seci.peekNextKey()
			items = seci.getNext()
			for item in items:
				typeName = item.key
				archName = item.value
				ogre.ResourceGroupManager.getSingleton().addResourceLocation(archName, typeName, secName)

	def _createResourceListener(self):
		"""Override to add a resource listener to check the status of resources loading"""
		pass

	def _loadResources(self):
		"""This loads all initial resources
		
		Redefine this if you do not want to load all resources at startup.
		
		"""
		ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()

	def _configure(self):
		"""This shows the config dialog and creates the render window"""
		if os.path.exists("ogre.cfg"):
			carryOn = self.root.restoreConfig()
		else:
			carryOn = self.root.showConfigDialog()

		if carryOn:
			self.renderWindow = self.root.initialise(True, self.window_title)
			settings.render_window = self.renderWindow
			settings.render_system = self.root.getRenderSystem()
		return carryOn

	def _createSoundManager(self):
		"""Creates the sound manager"""
		settings.sound_devices = ogreal.SoundManager.getDeviceList()

		import os.path
		if os.path.exists("sound.cfg"):
			config = ogre.ConfigFile()
			config.loadDirect("sound.cfg")
			settings.current_sound_device = config.getSetting("Device")
			if settings.current_sound_device == "":
				settings.music = False
				settings.sound_effects = False
				return
			music = config.getSetting("Music")
			if music == "Yes":
				settings.music = True
			else:
				settings.music = False
			
			sound = config.getSetting("Sound")
			if sound == "Yes":
				settings.sound_effects = True
			else:
				settings.sound_effects = False
		else:
			settings.current_sound_device = "Generic Software"
		self.soundManager = ogreal.SoundManager(settings.current_sound_device)

	def _chooseSceneManager(self):
		"""Chooses a default scene manager"""
		self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "DefaultSM")

	def _createCamera(self):
		"""Creates the camera"""
		self.camera = self.sceneManager.createCamera('PlayerCam')
		self.camera.position = (0, 0, 500)
		self.camera.lookAt((0, 0, -300))
		self.camera.nearClipDistance = 5

	def _createViewports(self):
		"""Creates the viewport"""
		self.viewport = self.renderWindow.addViewport(self.camera)
		self.viewport.backgroundColour = (0,0,0)
		
	def _createScene(self):
		"""Creates the scene
		
		Override this with initial scene contents.
		
		"""
		pass

	def update(self, evt):
		if hasattr(self, "currentScene"):
			return self.currentScene.update(evt)
		return True

	def _createFrameListener(self):
		"""Creates the frame listener"""
		self.frameListener = FrameListener(self.renderWindow, self.camera)
		self.frameListener.showDebugOverlay(True)
		self.root.addFrameListener(self.frameListener)

	def _isPsycoEnabled(self):
		"""Override this function and return True to turn on Psyco"""
		return False

	def _activatePsyco(self):		
	   """Import Psyco if available"""
	   try:
		   import psyco
		   psyco.full()
	   except ImportError:
		   pass

class FrameListener(ogre.FrameListener):
	"""A default frame listener, which takes care of basic mouse and keyboard input"""

	def __init__(self, renderWindow, camera):
		ogre.FrameListener.__init__(self)
		
		self.camera = camera
		self.renderWindow = renderWindow
		self.statisticsOn = True
		self.numScreenShots = 0
		self.timeUntilNextToggle = 0
		self.sceneDetailIndex = 0
		self.moveScale = 0.0
		self.rotationScale = 0.0
		self.translateVector = ogre.Vector3(0.0,0.0,0.0)
		self.filtering = ogre.TFO_BILINEAR
		self.showDebugOverlay(True)
		self.moveSpeed = 100.0
		self.rotationSpeed = 8.0
		self.renderWindow.debugText = ""

		self._setupInput()

	def _setupInput(self):
		"""Override to setup input for the listener"""
		pass

	def frameEnded(self, frameEvent):
		"""Called at the end of a frame"""
		self._updateStatistics()
		return True

	def showDebugOverlay(self, show):
		"""Turns the debug overlay (frame statistics) on or off"""
		overlay = ogre.OverlayManager.getSingleton().getByName('Core/DebugOverlay')
		if overlay is None:
			raise ogre.Exception(111, "Could not find overlay Core/DebugOverlay", "Framework.py")
		if show:
			overlay.show()
		else:
			overlay.hide()

	def _updateStatistics(self):
		"""Updates information in the debug overlay"""
		statistics = self.renderWindow
		self._setGuiCaption('Core/AverageFps', 'Average FPS: %f' % statistics.averageFPS)
		self._setGuiCaption('Core/CurrFps', 'Current FPS: %f' % statistics.lastFPS)
		self._setGuiCaption('Core/BestFps',
							 'Best FPS: %f %d ms' % (statistics.bestFPS, statistics.bestFrameTime))
		self._setGuiCaption('Core/WorstFps',
							 'Worst FPS: %f %d ms' % (statistics.worstFPS, statistics.worstFrameTime))
		self._setGuiCaption('Core/NumTris', 'Triangle Count: %d' % statistics.triangleCount)
		self._setGuiCaption('Core/DebugText', statistics.debugText)

	def _setGuiCaption(self, elementName, text):
		"""Sets the caption for an overlay element"""
		element = ogre.OverlayManager.getSingleton().getOverlayElement(elementName, False)
		element.caption = text

class CEGUIFrameListener(FrameListener, ois.MouseListener, ois.KeyListener):
	"""A frame listener which passes input to CEGUI and the current scene"""

	def __init__(self, application, renderWindow, camera):
		ois.MouseListener.__init__(self)
		ois.KeyListener.__init__(self)
		FrameListener.__init__(self, renderWindow, camera)

		self.application = application
		self.keepRendering = True   # whether to continue rendering or not
		self.sceneDetailIndex = 0
		self.ceguiTimer = ogre.Timer()

		root = self.application.root
		self.console = console.Console(root)
		self.console.addLocals({'root':root})
		self.console.addLocals({'app':application})

		wm = cegui.WindowManager.getSingleton()
		self.fps = wm.createWindow("SleekSpace/StaticText", "fps_counter")
		self.fps.position = cegui.UVector2(cegui.UDim(0.9, 0), cegui.UDim(0.0, 0))
		self.fps.size = cegui.UVector2(cegui.UDim(0.1, 0), cegui.UDim(0.1, 0))
		self.application.guiSystem.getGUISheet().addChildWindow(self.fps)
		self.fps.setVisible(settings.show_fps)

	def _setupInput(self):
		"""Setup the OIS library for input"""
		options = [("WINDOW", str(self.renderWindow.getCustomAttributeInt("WINDOW")))]

		if os.name.startswith("posix"):
			options.append(("x11_mouse_grab", str("false")))
		elif os.name.startswith("nt"):
			pass
			# FIXME: mouse problems in windows
			#options.append(("w32_mouse", str("DISCL_FOREGROUND")))
			#options.append(("w32_mouse", str("DISCL_NONEXCLUSIVE")))

		self.inputManager = ois.createPythonInputSystem(options)
		self.enableKeyboard = True
		self.enableMouse = True
	
		if self.enableKeyboard:
			self.keyboard = self.inputManager.createInputObjectKeyboard(
				ois.OISKeyboard, True)
			self.keyboard.setEventCallback(self)

		if self.enableMouse:
			self.mouse = self.inputManager.createInputObjectMouse(
				ois.OISMouse, True)
			
			self.mouse.setEventCallback(self)
			state = self.mouse.getMouseState()
			state.width = self.renderWindow.getWidth()
			state.height = self.renderWindow.getHeight()

	def destroy(self):
		"""Release OIS resources"""
		try:
			if self.inputManager != None:
				if self.enableKeyboard:
					self.inputManager.destroyInputObjectKeyboard(self.keyboard)
				if self.enableMouse:
					self.inputManager.destroyInputObjectMouse(self.mouse)
				ois.InputManager.destroyInputSystem(self.inputManager)
				self.keyboard = None
				self.mouse = None
				self.inputManager = None
		except AttributeError:
			pass

	def frameStarted(self, evt):
		"""Called at the start of a frame"""
		self.application.frameStarted(evt)
		if self.renderWindow.isClosed():
			self.keepRendering = False
		
		if self.keepRendering:
			if settings.show_fps:
				self.fps.setText("fps: %d" % self.renderWindow.getAverageFPS())

			cegui.System.getSingleton().injectTimePulse(self.ceguiTimer.getMilliseconds() / 1000)
			self.ceguiTimer.reset()
			if self.enableMouse and self.mouse != None:
				self.mouse.capture()

			if self.enableKeyboard and self.keyboard != None:
				self.keyboard.capture()
				self.keyDown()
		
		return self.application.update(evt) and self.keepRendering

	def mouseDragged(self, evt):
		"""Passes MouseDragged events to CEGUI and then the current scene"""
		system = cegui.System.getSingleton()
		system.injectMouseMove(evt.relX * system.renderer.width, evt.relY * system.renderer.height) \
			or self.application.currentScene.mouseDragged(evt)

	def mousePressed(self, evt, id):
		"""Passes MousePressed events to CEGUI and then the current scene"""
		button = self._convertOgreButtonToCegui(id)
		cegui.System.getSingleton().injectMouseButtonDown(button) \
			or self.application.currentScene.mousePressed(evt, id)

	def mouseReleased(self, evt, id):
		"""Passes MouseReleased events to CEGUI and then the current scene"""
		button = self._convertOgreButtonToCegui(evt)
		cegui.System.getSingleton().injectMouseButtonUp(button) \
			or self.application.currentScene.mouseReleased(evt, id)

	def mouseMoved(self, evt):
		"""Passes MouseMoved events to CEGUI and then the current scene"""
		system = cegui.System.getSingleton()
		system.injectMousePosition(evt.get_state().X.abs, evt.get_state().Y.abs) \
			or self.application.currentScene.mouseMoved(evt)
		return True

	def keyPressed(self, evt):
		"""Handles a single key press by the user"""
		if self.console.keyPressed(evt):
			return True

		if evt.key == ois.KC_F12:
			path, next = 'screenshot.png', 1
			while os.path.exists(path):
				path = 'screenshot_%d.png' % next
				next += 1
			
			self.renderWindow.writeContentsToFile(path)
			self.renderWindow.debugText = 'screenshot taken: ' + path

		elif evt.key == ois.KC_Q:
			if self.keyboard.isKeyDown(ois.KC_LCONTROL) or self.keyboard.isKeyDown(ois.KC_RCONTROL):
				self.keepRendering = False
				return True

		# Debugging functions
		elif evt.key == ois.KC_SCROLL:
			detailsLevel = ("SDL_SOLID", "SDL_WIREFRAME", "SDL_POINTS")
			self.sceneDetailIndex += 1 
			self.sceneDetailIndex %= len(detailsLevel)
			
			mode = detailsLevel[self.sceneDetailIndex]
			self.camera.detailLevel = getattr(ogre, mode)
			self.renderWindow.debugText = 'render mode set to: ' + mode

		else:
			system = cegui.System.getSingleton()
			(system.injectKeyDown(evt.key) or system.injectChar(evt.text)) \
				or self.application.currentScene.keyPressed(evt)
		
		return True

	def keyReleased(self, evt):
		"""Handles a single key release by the user"""
		system = cegui.System.getSingleton()
		system.injectKeyUp(evt.key) \
			or self.application.currentScene.keyReleased(evt)

	def keyDown(self):
		"""Handles keys that are constantly held down"""
		self.application.currentScene.keyDown(self.keyboard)

	def _convertOgreButtonToCegui(self, buttonID):
		"""Convert ogre button to cegui button"""
		if buttonID ==0:
			return cegui.LeftButton
		elif buttonID ==1:
			return cegui.RightButton
		elif buttonID ==2:
			return cegui.MiddleButton
		elif buttonID ==3:
			return cegui.X1Button
		else:
			return cegui.LeftButton

