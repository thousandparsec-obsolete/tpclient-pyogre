# This code is in the Public Domain
# -----------------------------------------------------------------------------
# This source file is part of Python-Ogre
# For the latest info, see http://python-ogre.org/
#
# It is likely based on original code from OGRE and/or PyOgre
# For the latest info, see http://www.ogre3d.org/
#
# You may use this sample code for anything you like, it is not covered by the
# LGPL.
# -----------------------------------------------------------------------------

import ogre.renderer.OGRE as ogre

class LoadingBar():
	"""Defines an example loading progress bar

	Basically you just need to create an instance of this class, call start()
	before loading and finish() afterwards. You may also need to stop areas of
	your scene rendering in between since this method will call 
	RenderWindow.update() to update the display of the bar - we advise using
	SceneManager's 'special case render queues' for this, see
	SceneManager.addSpecialCaseRenderQueue for details.

	@note 
	  This progress bar relies on you having the OgreCore.zip package already 
	  added to a resource group called 'Bootstrap' - this provides the basic 
	  resources required for the progress bar and will be loaded automatically.

	"""

	def __init__(self):
		#ogre.ResourceGroupListener.__init__(self)
		self.started = False
		
	def start(self, window, numGroupsInit=1, numGroupsLoad=1, initProportion=0.70):
		"""Show the loading bar and start listening

		   @param window The window to update 
		   @param numGroupsInit The number of groups you're going to be initialising
		   @param numGroupsLoad The number of groups you're going to be loading
		   @param initProportion The proportion of the progress which will be taken
			   up by initialisation (ie script parsing etc). Defaults to 0.7 since
			   script parsing can often take the majority of the time.

		"""
		self.mWindow = window
		self.mNumGroupsInit = numGroupsInit
		self.mNumGroupsLoad = numGroupsLoad
		self.mInitProportion = initProportion
		# We need to pre-initialise the 'Bootstrap' group so we can use
		# the basic contents in the loading screen
		ogre.ResourceGroupManager.getSingleton().initialiseResourceGroup("Bootstrap")

		omgr = ogre.OverlayManager.getSingleton()
		self.mLoadOverlay = omgr.getByName("Core/LoadOverlay")
		if ( not self.mLoadOverlay):
			raise OGRE_EXCEPT(Exception.ERR_ITEM_NOT_FOUND, 
				"Cannot find loading overlay", "ExampleLoadingBar.start")
		self.mLoadOverlay.show()

		# Save links to the bar and to the loading text, for updates as we go
		self.mLoadingBarElement = omgr.getOverlayElement("Core/LoadPanel/Bar/Progress")
		self.mLoadingCommentElement = omgr.getOverlayElement("Core/LoadPanel/Comment")
		self.mLoadingDescriptionElement = omgr.getOverlayElement("Core/LoadPanel/Description")

		barContainer = omgr.getOverlayElement("Core/LoadPanel/Bar")
		self.mProgressBarMaxSize = barContainer.getWidth()
		self.mLoadingBarElement.setWidth(0)

		# self is listener for callbacks from resource loading
		#ogre.ResourceGroupManager.getSingleton().addResourceGroupListener(self)

	def show(self):
		self.mLoadOverlay.show()
		self.started = True

	def finish(self):
		"""Hide the loading bar and stop listening"""
		# hide loading screen
		self.mLoadOverlay.hide()

		self.started = False

		# Unregister listener
		#ogre.ResourceGroupManager.getSingleton().removeResourceGroupListener(self)

	def setCaption(self, text):
		self.mLoadingCommentElement.setCaption(ogre.UTFString(text))

	def setTitle(self, text):
		self.mLoadingDescriptionElement.setCaption(ogre.UTFString(text))
	
	def advance(self):
		self.mProgressBarInc = self.mProgressBarMaxSize / self.mNumGroupsInit
		bar_width = self.mLoadingBarElement.getWidth() + self.mProgressBarInc
		if bar_width > self.mProgressBarMaxSize:
			bar_width = self.mProgressBarMaxSize
		self.mLoadingBarElement.setWidth(bar_width)
	
	# ResourceGroupListener callbacks
	def resourceGroupScriptingStarted(self, groupName, scriptCount):
		if self.mNumGroupsInit > 0 and scriptCount > 0:
			# Lets assume script loading is 70%
			self.mProgressBarInc = self.mProgressBarMaxSize * self.mInitProportion / scriptCount
			self.mProgressBarInc /= self.mNumGroupsInit
			self.mLoadingDescriptionElement.setCaption(ogre.UTFString("Parsing scripts.."))
			self.mWindow.update()
	
	def scriptParseStarted(self, scriptName):
		self.mLoadingCommentElement.setCaption(ogre.UTFString(scriptName))
		self.mWindow.update()

	def scriptParseEnded(self, scriptName):
		self.mLoadingBarElement.setWidth(
			self.mLoadingBarElement.getWidth() + self.mProgressBarInc)
		self.mWindow.update()

	def resourceGroupScriptingEnded(self, groupName):
		pass
	
	def resourceGroupLoadStarted(self, groupName, resourceCount):
		ogre.LogManager.getSingleton().logMessage("GroupLoadStarted " + groupName )
		if self.mNumGroupsLoad >0 :
			self.mProgressBarInc = self.mProgressBarMaxSize * (1-self.mInitProportion) / resourceCount
			self.mProgressBarInc /= self.mNumGroupsLoad
			self.mLoadingDescriptionElement.setCaption(ogre.UTFString("Loading resources.."))
			self.mWindow.update()
		
	def resourceLoadStarted(self, resource):
		ogre.LogManager.getSingleton().logMessage("GroupLoadEnded" )
		self.mLoadingCommentElement.setCaption(ogre.UTFString(resource.getName()))
		self.mWindow.update()
	
	def resourceLoadEnded(self):
		pass
		
	def worldGeometryStageStarted(self, description):
		ogre.LogManager.getSingleton().logMessage("StageStarted " + description )
		self.mLoadingCommentElement.setCaption(ogre.UTFString(description))
		self.mWindow.update()
		
	def worldGeometryStageEnded(self):
		ogre.LogManager.getSingleton().logMessage("StageEnded")
		self.mLoadingBarElement.setWidth(
			self.mLoadingBarElement.getWidth() + self.mProgressBarInc)
		self.mWindow.update()
		
	def resourceGroupLoadEnded(self, groupName):
		pass

