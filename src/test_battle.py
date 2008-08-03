#! /usr/bin/env python

import os
import sys
import math

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui
import ogre.io.OIS as ois

import framework
import scene
import helpers
import starmap
import battlexml.battle as battle

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

class BattleScene(scene.Scene):
	media = {
			'battleship':('plowshare', 75),
			'planet':('sphere_lod', 1500),
			'frigate':('frigate', 75),
			'scout':('scout', 50),
		}

	def __init__(self, parent, sceneManager):
		scene.Scene.__init__(self, parent, sceneManager)
		self.battle = None
		self.background_nodes = []
		self.sides = []
		self.bg_particle = None
		self.nodes = {}

		self.camera_focus_node = self.rootNode.createChildSceneNode("CameraFocus")
		self.camera_node = self.camera_focus_node.createChildSceneNode("CameraNode")
		self.camera_node.attachObject(self.camera)
		self.camera_target_node = self.camera_focus_node.createChildSceneNode("CameraTarget")
		self.camera_target_node.position = self.camera_node.position
		self.h_angle = 0
		self.v_angle = 0

		self.createBackground()
		self.hide()

	def create(self, file_name):
		self.battle = battle.parse_file(file_name)
		for side in self.battle.sides:
			self.createSide(side)
		self.setStartingPositions(500)
		self.autofit()

	def setStartingPositions(self, radius):
		i = 1
		spacing = 360 / len(self.sides)
		for side in self.sides:
			interval = spacing * i
			interval = math.radians(interval)
			x = radius * math.cos(interval)
			y = radius * math.sin(interval)
			side.position = [x, y, 0]
			#side.lookAt(ogre.Vector3(0, 0, 0), ogre.SceneNode.TransformSpace.TS_WORLD)
			i += 1

	def createSide(self, side):
		print "creating side", side.id
		side_node = self.rootNode.createChildSceneNode("%s_node" % side.id)
		i = 0
		for entity in side.entities:
			i += 1
			print "creating", entity.name, entity.type
			node = side_node.createChildSceneNode("%s_node" % entity.id)
			media = self.media[entity.type]
			mesh = "%s.mesh" % media[0]
			entity_object = self.sceneManager.createEntity("%s" % entity.id, mesh)
			entity_object.setNormaliseNormals(True)
			if entity.type == 'planet':
				entity_object.setMaterialName("Starmap/Planet/Terran")
				node.position = [-media[1] / 2 - media[1], 0, 0]
				#node.yaw(ogre.Radian(1.57))
			else:
				node.position = [0, i * 100, 0]
				node.yaw(ogre.Radian(1.57))
				node.roll(ogre.Radian(1.57))

				# orient ships to face each other
				node.yaw(ogre.Radian(3.13 * len(self.sides)))
				#node.pitch(ogre.Radian(3.14))
			obj_scale = media[1] / entity_object.mesh.boundingSphereRadius
			node.attachObject(entity_object)
			node.setScale(ogre.Vector3(obj_scale, obj_scale, obj_scale))
			self.nodes[entity.id] = node

		self.sides.append(side_node)

	def createBackground(self):
		"""Creates a starry background for the current scene"""
		if self.bg_particle is None:
			self.bg_particle = self.sceneManager.createParticleSystem("star_layer1", "Space/Stars/Large")
		self.bg_particle.keepParticlesInLocalSpace = True
		particleNode = self.sceneManager.getSceneNode("CameraNode").createChildSceneNode("StarryBackgroundLayer1")
		particleNode.attachObject(self.bg_particle)
		#self.sceneManager.getSceneNode("CameraFocus").attachObject(self.bg_particle)
		#self.background_nodes.append(particleNode)

	def mouseMoved(self, evt):
		"""Handles the MouseMoved event

		If the middle mouse button is down pan the screen.
		Scrolling the mousewheel will zoom in and out.

		"""
		state = evt.get_state()

		if state.buttonDown(ois.MB_Middle):
			self.pan(state.X.rel * 50, -state.Y.rel * 50)

		elif state.buttonDown(ois.MB_Right):
			self.rotate(state.X.rel, state.Y.rel)

		elif state.Z.rel < 0:
			self.zoom(1000)

		elif state.Z.rel > 0:
			self.zoom(-1000)

		return False

	def zoom(self, amount):
		"""Zoom in or out for a set amount. Negative amounts will zoom in."""
		target = self.sceneManager.getSceneNode("CameraNode")
		z = target.position.z
		target.translate(0, 0, amount)

	def pan(self, x, y):
		cam_focus = self.sceneManager.getSceneNode("CameraFocus")
		cam_focus.translate(x, y, 0, ogre.SceneNode.TransformSpace.TS_LOCAL)

	def rotate(self, h_angle, v_angle):
		cam_focus = self.sceneManager.getSceneNode("CameraFocus")
		self.v_angle += v_angle
		self.h_angle += h_angle
		q = ogre.Quaternion(ogre.Degree(self.h_angle), ogre.Vector3.UNIT_Z)
		r = ogre.Quaternion(ogre.Degree(self.v_angle), ogre.Vector3.UNIT_X)
		q = q * r
		cam_focus.setOrientation(q)

	def autofit(self):
		"""Zooms out until all stars are visible"""
		fit = False
		camera = self.sceneManager.getCamera("PlayerCam")
		camera_node = self.sceneManager.getSceneNode("CameraNode")
		camera_node.position = ogre.Vector3(0, 0, 0)
		while not fit:
			camera_node.translate(0, 0, 1000)

			fit = True
			for obj in self.nodes.values():
				if not camera.isVisible(obj.position):
					fit = False

class TestBattle(framework.Application):
	"""Display the starmap without using a network connection"""

	def __init__(self):
		framework.Application.__init__(self)
		
		self.guiRenderer = 0
		self.guiSystem = 0
		self.application = DummyApplication()
		self.application.cache = DummyCache()

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

		self.battle = BattleScene(self, self.sceneManager)
		self.battle.create("battlexml/example1.xml")
		self.changeScene(self.battle)

		self.guiSystem.injectMousePosition(0, 0)

	def _createCamera(self):
		self.camera = self.sceneManager.createCamera("PlayerCam")
		self.camera.nearClipDistance = 5
		self.camera.setFixedYawAxis(True, ogre.Vector3.UNIT_Y)

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
	app = TestBattle()
	app.go()
	app.Cleanup()
