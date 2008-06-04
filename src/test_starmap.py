#! /usr/bin/env python

import os
import sys

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

import Framework
import Scene
import helpers

class DummyCache(object):
	def __init__(self):
		objects = helpers.pickle_load("object")
		self.messages = [[]]
		self.objects = objects

class TestStarmap(Framework.Application):
	def __init__(self):
		Framework.Application.__init__(self)
		
		self.guiRenderer = 0
		self.guiSystem = 0

		self.tocall = []

	def _createScene(self):
		"""Setup CEGUI and create the various scenes"""
		# Initialise CEGUI Renderer
		self.guiRenderer = cegui.OgreCEGUIRenderer(self.renderWindow,
				   ogre.RENDER_QUEUE_OVERLAY, True, 0, self.sceneManager)
		self.guiSystem = cegui.System(self.guiRenderer)
		cegui.Logger.getSingleton().loggingLevel = cegui.Insane

		# Load Cegui Scheme
		cegui.SchemeManager.getSingleton().loadScheme("SleekSpace.scheme")
		self.guiSystem.setDefaultMouseCursor("SleekSpace", "MouseArrow")

		wmgr = cegui.WindowManager.getSingleton()
		root = wmgr.createWindow("DefaultWindow", "root")
		self.guiSystem.setGUISheet(root)

		self.starmap = Scene.StarmapScene(self, self.sceneManager)
		self.changeScene(self.starmap)
		dummy_cache = DummyCache()
		self.starmap.create(dummy_cache)

		self.guiSystem.injectMousePosition(0, 0)

	def _createCamera(self):
		self.camera = self.sceneManager.createCamera("PlayerCam")
		self.camera.nearClipDistance = 5
		self.camera.setFixedYawAxis(True, ogre.Vector3.UNIT_Y)

	def _createFrameListener(self):
		self.frameListener = Framework.CEGUIFrameListener(self, self.renderWindow, self.camera)
		self.root.addFrameListener(self.frameListener)
		self.frameListener.showDebugOverlay(False)

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
