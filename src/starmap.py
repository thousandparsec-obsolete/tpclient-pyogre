import math

import ogre.renderer.OGRE as ogre

import overlay

class Starmap(object):
	"""Responsible for handling the display of the starmap"""

	def __init__(self, parent, sceneManager, rootNode):
		self.parent = parent
		self.sceneManager = sceneManager
		self.rootNode = rootNode
		self.camera = self.sceneManager.getCamera( 'PlayerCam' )

		self.nodes = {}
		self.lines = 0
		self.overlays = {}
		self.bg_particle = None
		self.zoom = 0

	def createBackground(self):
		"""Creates a starry background for the current scene"""
		if self.bg_particle is None:
			self.bg_particle = self.sceneManager.createParticleSystem("stars", "Space/Stars")
		particleNode = self.rootNode.createChildSceneNode("StarryBackground")
		particleNode.pitch(ogre.Radian(1.57))
		particleNode.attachObject(self.bg_particle)

	def addStar(self, object, position):
		node = self.createObjectNode(position, object.id, 'sphere.mesh', 100)
		self.nodes[object.id] = node
		entityNode = self.sceneManager.getSceneNode("Object%i_EntityNode" % object.id)

		# Text overlays
		label = overlay.ObjectOverlay(entityNode, object)
		label.show(label.name)
		label.setColour(ogre.ColourValue(0.7, 0.9, 0.7))
		self.overlays[object.id] = label

		return node

	def addPlanet(self, object, position, parent):
		pos = self.calculateRadialPosition(position, 100, 720, parent.planets, object.index)
		node = self.createObjectNode(pos, object.id, 'sphere.mesh', 50)
		self.nodes[object.id] = node
		entity = self.sceneManager.getEntity("Object%i" % object.id)
		entity.setMaterialName("Starmap/Planet")

	def addFleet(self, object, position, parent):
		pos = self.calculateRadialPosition(position, 200, 360, parent.fleets, object.index)
		node = self.createObjectNode(pos, object.id, 'ship.mesh', 50)
		self.nodes[object.id] = node
		entityNode = node.getChild(0)
		entityNode.yaw(ogre.Radian(1.57))
		entityNode.roll(ogre.Radian(1.57))

	def setFleet(self, object, position, parent):
		pos = self.calculateRadialPosition(pos, 200, 360, parent.fleets, object.index)
		node = self.nodes[object.id]
		node.setPosition(pos)

	def mode(self, modes):
		if self.OWNERS in modes:
			for id, object in self.objects.items():
				if object.owner in (0, -1):
					self.overlays[id].colour = ogre.ColorValue.Blue
				else:
					self.overlays[id].colour = ogre.ColorValue.Yellow
		
	def createObjectNode(self, pos, oid, mesh, scale):
		"""Returns a scene node containing the scaled entity mesh
		
		pos - The current position of the object
		oid - The ID of the object
		mesh - String containing the mesh file name
		scale - How much to scale the object by

		"""
		node = self.rootNode.createChildSceneNode("Object%i_Node" % oid, pos)
		entityNode = node.createChildSceneNode("Object%i_EntityNode" % oid, ogre.Vector3(0, 0, 0))
		entity = self.sceneManager.createEntity("Object%i" % oid, mesh)
		obj_scale = scale / entity.mesh.boundingSphereRadius
		entityNode.setScale(ogre.Vector3(obj_scale, obj_scale, obj_scale))
		entityNode.attachObject(entity)
		return node

	def calculateRadialPosition(self, position, radius, total_degree, total_objects, object_index):
		"""Updates the position of an object orbiting around it's parent

		position - The current position of the object
		radius - The distance from the parent
		total_degree - How many total degrees there are
		total_objects - How many objects in total surrounding the parent
		object_index - Index of the current object
		
		"""
		interval = (total_degree / total_objects) * object_index
		x = radius * math.cos(interval)
		y = radius * math.sin(interval)
		position.x += x
		position.y += y
		return position

	def update(self):
		camera = self.sceneManager.getCamera( 'PlayerCam' )
		for label in self.overlays.values():
			label.update(camera)
		return True

	def drawLine(self, id_start, id_end):
		"""Draws a line showing the path of an object.

		id_start - ID of the moving object
		id_end - ID of the object's destination

		"""
		start_node = self.nodes[id_start]
		end_node = self.nodes[id_end]
		manual_object = self.sceneManager.createManualObject("line%i" % self.lines)
		scene_node = self.rootNode.createChildSceneNode("line%i_node" % self.lines)

		material = ogre.MaterialManager.getSingleton().create("line%i_material" % self.lines, "default")
		material.setReceiveShadows(False)
		material.getTechnique(0).getPass(0).setAmbient(0,1,0)

		manual_object.begin("line%i_material" % self.lines, ogre.RenderOperation.OT_LINE_LIST)
		manual_object.position(start_node.position)
		manual_object.position(end_node.position)
		manual_object.end()

		scene_node.attachObject(manual_object)
		self.lines += 1

	def clearLines(self):
		"""Removes all lines created by the drawLine method"""
		for i in range(self.lines):
			self.sceneManager.destroySceneNode("line%i_node" % i)
			self.sceneManager.destroyEntity("line%i" % i)
			ogre.MaterialManager.getSingleton().remove("line%i_material" % i)
		self.lines = 0

	def clearOverlays(self):
		"""Clears all the object labels"""
		for ov in self.overlays.values():
			ov.destroy()
		self.overlays = {}

	def clearObjects(self):
		for oid in self.nodes:
			self.sceneManager.destroyEntity("Object%i" % oid)
		self.rootNode.removeAndDestroyAllChildren()
		self.nodes = {}

	def autofit(self):
		"""Zooms out until all stars are visible"""
		fit = False
		self.camera.setPosition(ogre.Vector3(0,0,0))
		while not fit:
			self.camera.moveRelative(ogre.Vector3(0, 0, 500))

			fit = True
			for key in self.nodes:
				object = self.nodes[key]
				if not self.camera.isVisible(object.getPosition()):
					fit = False
		self.zoom = 0

	def center(self, id):
		"""Center on an object identified by object id"""
		node = self.nodes[id]
		pos = node.getPosition()
		cam = self.camera.getPosition()
		self.camera.setPosition(ogre.Vector3(pos.x,pos.y,cam.z))

