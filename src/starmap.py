import math
import random

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
		self.planets = []
		self.selection = {}

		self.flareBillboard = self.sceneManager.createBillboardSet("flare")
		self.flareBillboard.setMaterialName("Billboards/Flares/flare")
		self.flareBillboard.setCullIndividually(False)
		self.flareBillboard.setDefaultDimensions(500, 500)
		self.rootNode.attachObject(self.flareBillboard)

		self.selectionBillboard = self.sceneManager.createBillboardSet("selection")
		self.selectionBillboard.setMaterialName("Billboards/Selection")
		self.selectionBillboard.setCullIndividually(False)
		self.selectionBillboard.setDefaultDimensions(500, 500)
		self.rootNode.attachObject(self.selectionBillboard)

		self.sceneManager.ambientLight = (0, 0, 0)

		light = self.sceneManager.createLight('TopLight')
		light.type = ogre.Light.LT_DIRECTIONAL
		light.diffuseColour = (1, 1, 1)
		light.direction = (0, 0, -1)

	def createBackground(self):
		"""Creates a starry background for the current scene"""
		if self.bg_particle is None:
			self.bg_particle = self.sceneManager.createParticleSystem("star_layer1", "Space/Stars/Large")
		particleNode = self.rootNode.createChildSceneNode("StarryBackgroundLayer1")
		particleNode.pitch(ogre.Radian(1.57))
		particleNode.attachObject(self.bg_particle)
		self.bg_particle1 = self.sceneManager.createParticleSystem("stars_layer2", "Space/Stars/Small")
		particleNode = self.rootNode.createChildSceneNode("StarryBackgroundLayer2")
		particleNode.pitch(ogre.Radian(1.57))
		particleNode.attachObject(self.bg_particle1)

	def addStar(self, object, position):
		node = self.createObjectNode(position, object.id, 'sphere_lod.mesh', 100, False)
		self.nodes[object.id] = node
		entityNode = self.sceneManager.getSceneNode("Object%i_EntityNode" % object.id)

		# Lens flare
		billboard = self.flareBillboard.createBillboard(position, ogre.ColourValue.White)

		light = self.sceneManager.createLight("Object%i_Light" % object.id)
		light.type = ogre.Light.LT_POINT
		light.position = position
		light.setAttenuation(500, 1, 0, 0)

		# Text overlays
		label = overlay.ObjectOverlay(entityNode, object)
		label.show(label.name)
		label.setColour(ogre.ColourValue(0.7, 0.9, 0.7))
		self.overlays[object.id] = label

		random.seed(object.id)
		star_type = random.choice(["Orange", "White", "Green"])

		entity = self.sceneManager.getEntity("Object%i" % object.id)
		entity.setMaterialName("Starmap/Sun/%s" % star_type)

		return node

	def addPlanet(self, object, position, parent):
		pos = self.calculateRadialPosition(position, 300, 720, parent.planets, object.index)
		node = self.createObjectNode(pos, object.id, 'sphere_lod.mesh', 50)
		self.nodes[object.id] = node
		self.planets.append(node)
		entityNode = node.getChild(0)
		entityNode.pitch(ogre.Radian(1.57))

		random.seed(parent.id)
		for i in range(object.index):
			random.random()
		planet_type = random.choice(["Terran", "Ocean", "Arid"])

		entity = self.sceneManager.getEntity("Object%i" % object.id)
		entity.setMaterialName("Starmap/Planet/%s" % planet_type)

	def addFleet(self, object, position, parent, fleet_type = 0):
		# rotate between 3 ship types
		meshes = [('scout', 50), ('frigate', 75), ('plowshare', 75)]
		fleet_type %= len(meshes)
		mesh = meshes[fleet_type]
		pos = self.calculateRadialPosition(position, 200, 360, parent.fleets, object.index)
		node = self.createObjectNode(pos, object.id, '%s.mesh' % mesh[0], mesh[1])
		self.nodes[object.id] = node
		entityNode = node.getChild(0)
		entityNode.yaw(ogre.Radian(1.57))
		entityNode.roll(ogre.Radian(1.57))

		owner = object.owner
		random.seed(owner)
		entity = self.sceneManager.getEntity("Object%i" % object.id)
		material = entity.getSubEntity(0).getMaterial()
		material_name = "%s_%i" % (material.getName(), owner)
		material_manager = ogre.MaterialManager.getSingleton()
		if not material_manager.resourceExists(material_name):
			material = material.clone(material_name)
		else:
			material = material_manager.getByName(material_name)

		entity.setMaterialName(material_name)

		r = random.random
		#material.setDiffuse(r(), r(), r(), 1)

	def setFleet(self, object, position, parent):
		pos = self.calculateRadialPosition(position, 200, 360, parent.fleets, object.index)
		node = self.nodes[object.id]
		node.setPosition(pos)

	def hasObject(self, id):
		return id in self.nodes

	def selectObject(self, object_id, colour_value = ogre.ColourValue.White, scale_factor=3):
		"""Appends a scene node to the current selection and highlights it"""
		scene_node = self.nodes[object_id]
		position = scene_node.position
		scale = 20
		print scene_node, position, scale, scene_node.initialScale, scene_node.getChild(0).initialScale

		billboard = self.selectionBillboard.createBillboard(position, colour_value)
		billboard.setDimensions(scale * scale_factor, scale * scale_factor)

		self.selection[object_id] = billboard

	def unselectObject(self, object_id):
		"""Remove an object from the current selection"""
		if self.selection.has_key(object_id):
			billboard = self.selection[object_id]
			self.selectionBillboard.removeBillboard(billboard)
			del self.selection[object_id]

	def clearSelection(self):
		"""Clears all selected objects"""
		self.selectionBillboard.clear()
		self.selection = {}

	def mode(self, modes):
		if self.OWNERS in modes:
			for id, object in self.objects.items():
				if object.owner in (0, -1):
					self.overlays[id].colour = ogre.ColorValue.Blue
				else:
					self.overlays[id].colour = ogre.ColorValue.Yellow
		
	def createObjectNode(self, pos, oid, mesh, scale, normalise=True):
		"""Returns a scene node containing the scaled entity mesh
		
		pos - The current position of the object
		oid - The ID of the object
		mesh - String containing the mesh file name
		scale - How much to scale the object by
		normalise - Normalise normals if object uses lighting

		"""
		node = self.rootNode.createChildSceneNode("Object%i_Node" % oid, pos)
		entityNode = node.createChildSceneNode("Object%i_EntityNode" % oid, ogre.Vector3(0, 0, 0))
		entity = self.sceneManager.createEntity("Object%i" % oid, mesh)
		entity.setNormaliseNormals(normalise)
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
		camera = self.sceneManager.getCamera('PlayerCam')
		for label in self.overlays.values():
			label.update(camera)
		for planet in self.planets:
			planet.getChild(0).roll(ogre.Radian(0.005))

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

