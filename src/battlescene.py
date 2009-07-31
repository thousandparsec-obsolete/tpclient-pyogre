import math

import ogre.renderer.OGRE as ogre
import ogre.io.OIS as ois

import scene

from move import MoveFrameListener
from participant import Participant

class BattleScene(scene.Scene):
	media = {
			'battleship':('plowshare', 75),
			'planet':('sphere_lod', 1500),
			'frigate':('gawain', 50),
			'scout':('scout', 50),
		}

	def __init__(self, parent, sceneManager):
		scene.Scene.__init__(self, parent, sceneManager)
		self.background_nodes = []
		self.sides = []
		self.bg_particle = None
		self.nodes = {}
		self.userobjects = {}
		self.listeners = {}

		self.camera_focus_node = self.rootNode.createChildSceneNode("CameraFocus")
		self.camera_node = self.camera_focus_node.createChildSceneNode("CameraNode")
		self.camera_node.attachObject(self.camera)
		self.camera_target_node = self.camera_focus_node.createChildSceneNode("CameraTarget")
		self.camera_target_node.position = self.camera_node.position
		self.h_angle = 0
		self.v_angle = 0

		root = ogre.Root.getSingleton()
		self.mfl = MoveFrameListener()
		root.addFrameListener(self.mfl)

		self.zoomtimer = ogre.Timer()
		self.zoomstart = 0
		self.basezoom = 100

		#self.createBackground()
		self.hide()

	def initial(self, sides):
		for side in sides:
			self.createSide(side)
		self.setStartingPositions(500)
		self.autofit()
		return self

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
		cur_pos = 0
		for entity in side.entities:
			i += 1
			print "creating", entity.name, entity.type
			node = side_node.createChildSceneNode("%s_node" % entity.id)
			media = self.media[entity.type]
			mesh = "%s.mesh" % media[0]
			entity_object = self.sceneManager.createEntity("%s" % entity.id, mesh)
			#entity_object.setNormaliseNormals(True)
			if entity.type == 'planet':
				entity_object.setMaterialName("Starmap/Planet/Terran")
				node.position = [-media[1] / 2 - media[1], 0, 0]
				#node.yaw(ogre.Radian(1.57))
			else:
				cur_pos += media[1]*2+1
				node.position = [0, cur_pos, 0]
				node.yaw(ogre.Radian(1.57))
				node.roll(ogre.Radian(1.57))

				# orient ships to face each other
				node.yaw(ogre.Radian(3.13 * len(self.sides)))
				#node.pitch(ogre.Radian(3.14))
			obj_scale = media[1] / entity_object.mesh.boundingSphereRadius
			engine = self.sceneManager.createParticleSystem(entity.name + "/Engine", "%s/Engine" % "generic")
			engine.setVisible(False)
			userObject = Participant(entity_object, entity, engine)
			entity_object.setUserObject(userObject)
			self.mfl.registerEntity(entity_object, node)
			node.attachObject(entity_object)
			node.attachObject(engine)
			node.setScale(ogre.Vector3(obj_scale, obj_scale, obj_scale))
			self.userobjects[entity.id] = userObject
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
			self.zoom(1)

		elif state.Z.rel > 0:
			self.zoom(-1)

		return False

	def zoom(self, dir, amount=None):
		"""Zoom in or out for a set amount. Negative amounts will zoom in."""
		target = self.sceneManager.getSceneNode("CameraNode")
		z = target.position.z
		if amount:
			target.translate(0, 0, amount)
		else:
			curtime = self.zoomtimer.getMilliseconds()
			if curtime - self.zoomstart < 100 and self.prevdir == dir:
				self.zoomfactor += .1
				zoom = dir*self.basezoom**self.zoomfactor
				if zoom > 500:
					zoom = 500
				elif zoom < -500:
					zoom = -500
				target.translate(0, 0, zoom)
			else:
				self.prevdir = dir
				self.zoomfactor = 1
				self.zoomstart = self.zoomtimer.getMilliseconds()
				target.translate(0, 0, dir*self.basezoom/2)

	def pan(self, x, y):
		cam_focus = self.sceneManager.getSceneNode("CameraFocus")
		cam_focus.translate(x, y, 0, ogre.SceneNode.TransformSpace.TS_LOCAL)

	def rotate(self, h_angle, v_angle):
		cam_focus = self.sceneManager.getSceneNode("CameraFocus")
		self.v_angle += v_angle
		self.h_angle += h_angle
		q = ogre.Quaternion(ogre.Degree(self.h_angle), ogre.Vector3().UNIT_Z)
		r = ogre.Quaternion(ogre.Degree(self.v_angle), ogre.Vector3().UNIT_X)
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

