#! /usr/bin/env python

import os
import sys

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

import framework
import scene
import helpers

class DummyCache(object):
	def __init__(self):
		self.objects = helpers.pickle_load("object")
		self.messages = helpers.pickle_load("message")
		self.designs = helpers.pickle_load("design")
		self.players = helpers.pickle_load("player")
		self.resources = helpers.pickle_load("resource")
		self.orders = {}

class DummyApplication(object):
	pass

class TestStarmap(framework.Application):
	"""Display the starmap without using a network connection"""

	def __init__(self):
		framework.Application.__init__(self)
		
		self.guiRenderer = 0
		self.guiSystem = 0
		self.application = DummyApplication()
		self.application.cache = DummyCache()

		self.tocall = []

	def _createScene(self):
		"""Setup CEGUI and create the various scenes"""
		# Initialise CEGUI Renderer
		self.guiRenderer = cegui.OgreCEGUIRenderer(self.renderWindow,
				   ogre.RENDER_QUEUE_OVERLAY, True, 0, self.sceneManager)
		self.guiSystem = cegui.System(self.guiRenderer)
		cegui.Logger.getSingleton().loggingLevel = cegui.Insane

		# Load Cegui Scheme
		cegui.ImagesetManager.getSingleton().createImageset("thousandparsec.imageset")
		cegui.SchemeManager.getSingleton().loadScheme("SleekSpace.scheme")
		self.guiSystem.setDefaultMouseCursor("SleekSpace", "MouseArrow")

		wmgr = cegui.WindowManager.getSingleton()
		root = wmgr.createWindow("DefaultWindow", "root")
		self.guiSystem.setGUISheet(root)

		self.starmap = scene.StarmapScene(self, self.sceneManager)
		self.changeScene(self.starmap)
		self.starmap.create(self.application.cache)

		wmgr.getWindow("Windows").hide()

		self.guiSystem.injectMousePosition(0, 0)

		# Check shader syntax
		gpu = ogre.GpuProgramManager.getSingleton()
		syntaxi = gpu.getSupportedSyntax()
		for syntax in syntaxi:
			print "Supported shader syntax: ", syntax

	def _createCamera(self):
		self.camera = self.sceneManager.createCamera("PlayerCam")
		self.camera.setFixedYawAxis(True, ogre.Vector3.UNIT_Y)
		self.camera.setNearClipDistance(5)
		self.camera.setFarClipDistance(0)

	def _createFrameListener(self):
		self.frameListener = framework.CEGUIFrameListener(self, self.renderWindow, self.camera)
		self.root.addFrameListener(self.frameListener)
		self.frameListener.showDebugOverlay(True)

	def __del__(self):
		"""Clear variables
		
		This is needed to ensure the correct order of deletion.
		
		"""
		del self.camera
		del self.sceneManager
		del self.frameListener
		del self.guiSystem
		del self.guiRenderer
		del self.root
		del self.renderWindow		

	def frameStarted(self, evt):
		if not self.frameListener.keepRendering:
			print "destroying"
			self.frameListener.destroy()

		if len(self.tocall) <= 0:
			return
			
	def Cleanup(self):
		self.frameListener.keepRendering = False
		self.frameListener.destroy()

	def changeScene(self, scene):
		"""Function to change to a different scene"""
		if hasattr(self, "currentScene"):
			self.currentScene.hide()
		self.currentScene = scene
		self.currentScene.show()

if __name__ == '__main__':
	app = TestStarmap()
	app.go()
	app.Cleanup()
