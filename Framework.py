from pyogre import ogre, cegui

class Application(object):
    "This class is the base for an Ogre application."
    def __init__(self):
        self.frameListener = None
        self.root = None
        self.camera = None
        self.renderWindow = None
        self.sceneManager = None

    def __del__(self):
        "Clear variables, this should not actually be needed."
        del self.camera
        del self.sceneManager
        del self.frameListener
        del self.root
        del self.renderWindow

    def go(self):
        "Starts the rendering loop."
        if not self._setUp():
            return
        if self._isPsycoEnabled():
            self._activatePsyco()
        self.root.startRendering()

    def _setUp(self):
        """This sets up the ogre application, and returns false if the user
        hits "cancel" in the dialog box."""
        self.root = ogre.Root(ogre.getPluginPath())

        self._setUpResources()
        if not self._configure():
            return False
        
        self._chooseSceneManager()
        self._createCamera()
        self._createViewports()

        ogre.TextureManager.getSingleton().defaultNumMipmaps = 5

        self._createResourceListener()
        self._loadResources()

        self._createScene()
        self._createFrameListener()
        return True

    def _setUpResources(self):
        """This sets up Ogre's resources, which are required to be in
        resources.cfg."""
        config = ogre.ConfigFile()
        config.loadFromFile('resources.cfg' )
        for section, key, path in config.values:
            ogre.ResourceGroupManager.getSingleton().addResourceLocation(path, key, section)

    def _createResourceListener(self):
        """This method is here if you want to add a resource listener to check
        the status of resources loading."""
        pass

    def _loadResources(self):
        """This loads all initial resources.  Redefine this if you do not want
        to load all resources at startup."""
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()

    def _configure(self):
        """This shows the config dialog and creates the renderWindow."""
        carryOn = self.root.showConfigDialog()
        if carryOn:
            self.renderWindow = self.root.initialise(True)
        return carryOn

    def _chooseSceneManager(self):
        """Chooses a default SceneManager."""
        self.sceneManager = self.root.getSceneManager(ogre.ST_GENERIC)

    def _createCamera(self):
        """Creates the camera."""        
        self.camera = self.sceneManager.createCamera('PlayerCam')
        self.camera.position = (0, 0, 500)
        self.camera.lookAt((0, 0, -300))
        self.camera.nearClipDistance = 5

    def _createViewports(self):
        """Creates the Viewport."""
        self.viewport = self.renderWindow.addViewport(self.camera)
        self.viewport.backgroundColour = (0,0,0)
        
    def _createScene(self):
        """Creates the scene.  Override this with initial scene contents."""
        pass

    def _createFrameListener(self):
        """Creates the FrameListener."""
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

class FrameListener(ogre.CombinedListener):
    """A default frame listener, which takes care of basic mouse and keyboard
    input."""
    def __init__(self, renderWindow, camera):
        ogre.CombinedListener.__init__(self)
		
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

        self._setupInput()

    def _setupInput(self):
		pass

    def frameEnded(self, frameEvent):
        self._updateStatistics()
        return True

    def showDebugOverlay(self, show):
        """Turns the debug overlay (frame statistics) on or off."""
        overlay = ogre.OverlayManager.getSingleton().getByName('Core/DebugOverlay')
        if overlay is None:
            raise ogre.Exception(111, "Could not find overlay Core/DebugOverlay", "SampleFramework.py")
        if show:
            overlay.show()
        else:
            overlay.hide()

    def _updateStatistics(self):
        statistics = self.renderWindow
        self._setGuiCaption('Core/AverageFps', 'Average FPS: %f' % statistics.averageFPS)
        self._setGuiCaption('Core/CurrFps', 'Current FPS: %f' % statistics.lastFPS)
        self._setGuiCaption('Core/BestFps',
                             'Best FPS: %f %d ms' % (statistics.bestFPS, statistics.bestFrameTime))
        self._setGuiCaption('Core/WorstFps',
                             'Worst FPS: %f %d ms' % (statistics.worstFPS, statistics.worstFrameTime))
        self._setGuiCaption('Core/NumTris', 'Triangle Count: %d' % statistics.triangleCount)
        self._setGuiCaption('Core/DebugText', self.renderWindow.debugText)

    def _setGuiCaption(self, elementName, text):
        element = ogre.OverlayManager.getSingleton().getOverlayElement(elementName, False)
        element.caption = text

class CEGUIFrameListener(FrameListener):
	def __init__(self, application, renderWindow, camera):
		FrameListener.__init__(self, renderWindow, camera)

		self.application = application
		self.keepRendering = True   # whether to continue rendering or not
		self.sceneDetailIndex = 0

	def _setupInput(self):
		self.eventProcessor = ogre.EventProcessor()
		self.eventProcessor.initialise(self.renderWindow)
		self.eventProcessor.startProcessingEvents()

		# register as a listener for events
		self.eventProcessor.addKeyListener(self)
		self.eventProcessor.addMouseListener(self)
		self.eventProcessor.addMouseMotionListener(self)

	def frameStarted(self, evt):
		self.application.frameStarted(evt)
		return self.application.currentScene.update(evt) and self.keepRendering

	def mouseDragged(self, evt):
		system = cegui.System.getSingleton()
		system.injectMouseMove(evt.relX * system.renderer.width, evt.relY * system.renderer.height) \
			or self.application.currentScene.mouseDragged(evt)

	def mousePressed(self, evt):
		button = self._convertOgreButtonToCegui(evt)
		cegui.System.getSingleton().injectMouseButtonDown(button) \
			or self.application.currentScene.mousePressed(evt)

	def mouseReleased(self, evt):
		button = self._convertOgreButtonToCegui(evt)
		cegui.System.getSingleton().injectMouseButtonUp(button) \
			or self.application.currentScene.mouseReleased(evt)

	def mouseMoved(self, evt):
		system = cegui.System.getSingleton()
		system.injectMouseMove(evt.relX * system.renderer.width, evt.relY * system.renderer.height) \
			or self.application.currentScene.mouseMoved(evt)

	def keyPressed(self, evt):
		# Quick escape? Maybe it should be removed
		if evt.key == ogre.KC_ESCAPE:
			self.keepRendering = False
		
		if evt.key == ogre.KC_SYSRQ:
			path, next = 'screenshot.png', 1
			while os.path.exists(path):
				path = 'screenshot_%d.png' % next
				next += 1
			
			self.renderWindow.writeContentsToFile(path)
			self.renderWindow.debugText = 'screenshot taken: ' + path

		# Debugging functions
		if evt.key == ogre.KC_SCROLL:
			detailsLevel = ("SDL_SOLID", "SDL_WIREFRAME", "SDL_POINTS")
			self.sceneDetailIndex += 1 
			self.sceneDetailIndex %= len(detailsLevel)
			
			mode = detailsLevel[self.sceneDetailIndex]
			self.camera.detailLevel = getattr(ogre, mode)
			self.renderWindow.debugText = 'render mode set to: ' + mode

		system = cegui.System.getSingleton()
		(system.injectKeyDown(evt.key) or system.injectChar(evt.keyChar)) \
			or self.application.currentScene.keyPressed(evt)
		evt.consume()

	def keyReleased(self, evt):
		system = cegui.System.getSingleton()
		system.injectKeyUp(evt.key) \
			or self.application.currentScene.keyReleased(evt)

	# These are useless handlers that we need to have	
	def mouseClicked(self, evt):
		pass
	def mouseEntered(self, evt):
		pass
	def mouseExited(self, evt):
		pass
	def keyClicked(self, evt):
		pass

	def _convertOgreButtonToCegui(self,evt):
		# Convert ogre button to cegui button
		if (evt.buttonID & ogre.MouseEvent.BUTTON0_MASK):
			return cegui.LeftButton		
		elif (evt.buttonID & ogre.MouseEvent.BUTTON1_MASK):
			return cegui.RightButton		
		elif (evt.buttonID & ogre.MouseEvent.BUTTON2_MASK):
			return cegui.MiddleButton
		elif (evt.buttonID & ogre.MouseEvent.BUTTON3_MASK):
			return cegui.X1Button
		return cegui.LeftButton
