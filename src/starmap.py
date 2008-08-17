import math
import random

import ogre.renderer.OGRE as ogre
import ogre.sound.OgreAL as ogreal

import overlay
import settings

class Starmap(object):
	"""Responsible for handling the display of the starmap"""
	default_zoom = 4000
	icon_switch_level = -10
	max_zoom_out = -20
	min_zoom_in = -1

	def __init__(self, parent, sceneManager, rootNode):
		self.parent = parent
		self.sceneManager = sceneManager
		self.rootNode = rootNode

		self.nodes = {}
		self.lines = 0
		self.overlays = {}
		self.bg_particle = None
		self.background_nodes = []
		self.zoom_level = 0
		self.planets = []
		self.fleets = []
		self.fleet_colours = []
		self.stars = []
		self.selection = {}
		self.icons = {}
		self.sounds = {}
		self.show_icon = False
		self.last_clicked = None
		self.last_clicked_selection = None

		self.map_lower_left = [0, 0]
		self.map_upper_right = [0, 0]
		self.bounding_box = None
		self.h_angle = 0
		self.v_angle = 0

		self.raySceneQuery = self.sceneManager.createRayQuery(ogre.Ray())
		self.raySceneQuery.setSortByDistance(True, 10)
		self.raySceneQuery.setQueryMask(self.parent.SELECTABLE)

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

	def queryObjects(self, x, y):
		camera = self.sceneManager.getCamera("PlayerCam")
		mouseRay = camera.getCameraToViewportRay(x, y)
		self.raySceneQuery.setRay(mouseRay)
		mouseover_id = None
		for o in self.raySceneQuery.execute():
			if o.movable:
				mouseover_id = self.parent.getIDFromMovable(o.movable)
				break
		return mouseover_id

	def updateMapExtents(self):
		for obj in self.nodes.values():
			if obj.position.x < self.map_lower_left[0]:
				self.map_lower_left[0] = obj.position.x
			if obj.position.y < self.map_lower_left[1]:
				self.map_lower_left[1] = obj.position.y
			if obj.position.x > self.map_upper_right[0]:
				self.map_upper_right[0] = obj.position.x
			if obj.position.x > self.map_upper_right[1]:
				self.map_upper_right[1] = obj.position.y

	def updateBoundingBox(self):
		max_zoom = abs(self.max_zoom_out * 1000)
		min_zoom = abs(self.min_zoom_in * 1000)
		maxima = ogre.Vector3(self.map_upper_right[0], self.map_upper_right[1], max_zoom)
		minima = ogre.Vector3(self.map_lower_left[0], self.map_lower_left[1], min_zoom)
		self.bounding_box = ogre.AxisAlignedBox(minima, maxima)

	def show(self):
		self.setOverlayVisibility(True)
		self.setIconVisibility(True)
		self.setObjectVisibility(True)
		self.setIconView(self.show_icon)

	def hide(self):
		self.setOverlayVisibility(False)
		self.setIconVisibility(False)
		self.setObjectVisibility(False)

	def setOverlayVisibility(self, visible):
		self.flareBillboard.setVisible(visible)
		self.selectionBillboard.setVisible(visible)
		for ov in self.overlays.values():
			ov.setVisible(visible)

	def setIconVisibility(self, visible):
		for icon in self.icons.values():
			icon.setVisible(visible)

	def setObjectVisibility(self, visible):
		for fleet in self.fleets:
			self.nodes[fleet].setVisible(visible)
		for planet in self.planets:
			planet.setVisible(visible)
		for star in self.stars:
			star.setVisible(visible)
		for bg in self.background_nodes:
			bg.setVisible(visible)

	def createBackground(self):
		"""Creates a starry background for the current scene"""
		if self.bg_particle is None:
			layer_name = "star_layer1"
			if self.sceneManager.hasParticleSystem(layer_name):
				self.bg_particle = self.sceneManager.getParticleSystem(layer_name)
			else:
				self.bg_particle = self.sceneManager.createParticleSystem(layer_name, "Space/Stars/Large")
				self.bg_particle.keepParticlesInLocalSpace = False
		node_name = "StarryBackgroundLayer1"
		if not self.sceneManager.hasSceneNode(node_name):
			particleNode = self.sceneManager.getSceneNode("CameraFocus").createChildSceneNode(node_name)
			particleNode.attachObject(self.bg_particle)
		else:
			particleNode = self.sceneManager.getSceneNode(node_name)
		self.background_nodes.append(particleNode)

	def addStar(self, object, position):
		node = self.createObjectNode(position, object.id, 'sphere_lod.mesh', 100, False)
		self.nodes[object.id] = node
		self.stars.append(node)
		entity_node = self.sceneManager.getSceneNode("Object%i_EntityNode" % object.id)

		# Lens flare
		billboard = self.flareBillboard.createBillboard(position, ogre.ColourValue.White)

		light = self.sceneManager.createLight("Object%i_Light" % object.id)
		light.type = ogre.Light.LT_POINT
		light.position = position
		light.setAttenuation(500, 1, 0, 0)

		# Text overlays
		label = overlay.ObjectOverlay(entity_node, object)
		label.show(label.name)
		label.setColour(ogre.ColourValue(0.7, 0.9, 0.7))
		self.overlays[object.id] = label

		icon = overlay.IconOverlay(entity_node, object, "Starmap/Icons/Stars")
		self.icons[object.id] = icon

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
		entity_node = self.sceneManager.getSceneNode("Object%i_EntityNode" % object.id)

		colour = None
		if object.owner != -1:
			random.seed(object.owner)
			r = random.random
			colour = ogre.ColourValue(r(), r(), r(), 1)

		icon = overlay.IconOverlay(entity_node, object, "Starmap/Icons/Planets", 15, 15, colour)
		self.icons[object.id] = icon

		random.seed(parent.id)
		for i in range(object.index):
			random.random()
		planet_type = random.choice(["Terran", "Ocean", "Arid"])

		entity = self.sceneManager.getEntity("Object%i" % object.id)
		entity.setMaterialName("Starmap/Planet/%s" % planet_type)

		return node

	def addFleet(self, object, position, parent, fleet_type=0, query_flag=None):
		# rotate between 3 ship types
		meshes = [('scout', 50), ('frigate', 75), ('plowshare', 75)]
		fleet_type %= len(meshes)
		mesh = meshes[fleet_type]
		pos = self.calculateRadialPosition(position, 200, 360, parent.fleets, object.index)
		node = self.createObjectNode(pos, object.id, '%s.mesh' % mesh[0], mesh[1])
		self.nodes[object.id] = node
		self.fleets.append(object.id)
		entity_node = self.sceneManager.getSceneNode("Object%i_EntityNode" % object.id)
		entity_node.yaw(ogre.Radian(1.57))
		entity_node.roll(ogre.Radian(1.57))
		target_node = node.createChildSceneNode("Object%i_Target" % object.id, pos)

		# create a copy of the entity material so we can change it's colour
		owner = object.owner
		random.seed(owner)
		entity = self.sceneManager.getEntity("Object%i" % object.id)
		if query_flag:
			entity.setQueryFlags(query_flag)
		material = entity.getSubEntity(0).getMaterial()
		material_name = "%s_%i" % (material.getName(), owner)
		material_manager = ogre.MaterialManager.getSingleton()
		if not material_manager.resourceExists(material_name):
			material = material.clone(material_name)
			self.fleet_colours.append(material)
		else:
			material = material_manager.getByName(material_name)

		entity.setMaterialName(material_name)

		r = random.random
		colour = ogre.ColourValue(r(), r(), r(), 1)
		material.setDiffuse(colour)

		icon = overlay.IconOverlay(entity_node, object, "Starmap/Icons/Fleets", 20, 20, colour)
		self.icons[object.id] = icon

		#if settings.sound_effects:
			#sm = ogreal.SoundManager.getSingleton()
			#sound_name = "roar_%d" % object.id
			#if sm.hasSound(sound_name):
				#engine_fx = sm.getSound(sound_name)
			#else:
				#engine_fx = sm.createSound(sound_name, "roar.ogg", True)
				#engine_fx.setGain(0.5)
				#engine_fx.setRolloffFactor(5)
			#node.attachObject(engine_fx)
			#self.sounds[object.id] = engine_fx

		return node

	def setFleet(self, object, position, parent):
		pos = self.calculateRadialPosition(position, 200, 360, parent.fleets, object.index)
		target = self.sceneManager.getSceneNode("Object%i_Target" % object.id)
		target.position = pos
		#node = self.nodes[object.id]
		#node.setPosition(pos)

	def hasObject(self, id):
		return id in self.nodes

	def queryIcons(self, x, y):
		elements = []
		for icon in self.icons.values():
			element = icon.overlay.findElementAt(x, y)
			if element:
				elements.append(element)
		return elements

	def isIconClicked(self, x, y):
		#print "isIconClicked", x, y
		if not self.show_icon:
			return None

		elements = self.queryIcons(x, y)
		if len(elements) == 0:
			return None

		return_element = None

		# rotate through icons on the same spot
		if self.last_clicked and self.last_clicked[0] == x and self.last_clicked[1] == y:
			if self.last_clicked_selection < len(elements) - 1:
				self.last_clicked_selection += 1
			else:
				self.last_clicked_selection = 0
		else:
			self.last_clicked = [x, y]
			self.last_clicked_selection = 0

		return_element = elements[self.last_clicked_selection]
		return return_element

	def selectObject(self, object_id, colour_value=ogre.ColourValue.White, scale_factor=3):
		"""Appends a scene node to the current selection and highlights it"""
		scene_node = self.nodes[object_id]
		position = scene_node.position
		scale = 20
		print scene_node, position, scale, scene_node.initialScale, scene_node.getChild(0).initialScale

		billboard = self.selectionBillboard.createBillboard(position, colour_value)
		billboard.setDimensions(scale * scale_factor, scale * scale_factor)

		self.selection[object_id] = billboard
		if self.icons.has_key(object_id):
			self.icons[object_id].setHighlight(True)

	def unselectObject(self, object_id):
		"""Remove an object from the current selection"""
		if self.selection.has_key(object_id):
			billboard = self.selection[object_id]
			self.selectionBillboard.removeBillboard(billboard)
			del self.selection[object_id]

			if self.icons.has_key(object_id):
				self.icons[object_id].setHighlight(False)

	def clearSelection(self):
		"""Clears all selected objects"""
		self.selectionBillboard.clear()
		for id in self.selection.keys():
			if self.icons.has_key(id):
				self.icons[id].setHighlight(False)
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
		entity_node = node.createChildSceneNode("Object%i_EntityNode" % oid, ogre.Vector3(0, 0, 0))
		entity = self.sceneManager.createEntity("Object%i" % oid, mesh)
		entity.setNormaliseNormals(normalise)
		obj_scale = scale / entity.mesh.boundingSphereRadius
		entity_node.setScale(ogre.Vector3(obj_scale, obj_scale, obj_scale))
		entity_node.attachObject(entity)

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
		camera = self.sceneManager.getCamera("PlayerCam")
		self.parent.parent.renderWindow.debugText = "Z:%d" % self.zoom_level

		self.icon_switch_level = (abs(self.max_zoom_out) - abs(self.min_zoom_in)) * -settings.icon_zoom_switch_level
		if self.zoom_level < self.icon_switch_level:
			if not self.show_icon:
				self.setIconView(True)
		else:
			if self.show_icon:
				self.setIconView(False)
		
		for icon in self.icons.values():
			icon.update(camera)
		for label in self.overlays.values():
			label.update(camera)

		if not self.show_icon:
			for planet in self.planets:
				planet.getChild(0).roll(ogre.Radian(0.005))

		for fleet in self.fleets:
			node = self.sceneManager.getSceneNode("Object%i_Node" % fleet)
			target = self.sceneManager.getSceneNode("Object%i_Target" % fleet)
			move_speed = 100
			node_pos = node.position
			target_pos = target.position
			if node_pos != target_pos:
				if abs(node_pos.x - target_pos.x) < move_speed:
					node.position.x = target_pos.x
				elif node_pos.x < target_pos.x:
					node.translate(move_speed, 0, 0)
				elif node_pos.x > target_pos.x:
					node.translate(-move_speed, 0, 0)

				if abs(node_pos.y - target_pos.y) < move_speed:
					node.position.y = target_pos.y
				elif node_pos.y < target_pos.y:
					node.translate(0, move_speed, 0)
				elif node_pos.y > target_pos.y:
					node.translate(0, -move_speed, 0)

		return True

	def setIconView(self, visible):
		for fleet in self.fleets:
			self.nodes[fleet].setVisible(not visible)
		for planet in self.planets:
			planet.setVisible(not visible)
		for star in self.stars:
			star.setVisible(not visible)
		self.flareBillboard.setVisible(not visible)
		if not settings.show_stars_during_icon_view:
			for bg in self.background_nodes:
				bg.setVisible(not visible)
			self.sceneManager.setSkyBox(not visible, 'skybox/SpaceSkyBox')
		else:
			for bg in self.background_nodes:
				bg.setVisible(True)
			self.sceneManager.setSkyBox(True, 'skybox/SpaceSkyBox')
		self.selectionBillboard.setVisible(not visible)

		for icon in self.icons.values():
			icon.setVisible(visible)

		for sound in self.sounds.values():
			if visible:
				sound.stop()
			else:
				sound.play()

		self.show_icon = visible

	def drawLine(self, id_start, id_end):
		"""Draws a line showing the path of an object.

		id_start - ID of the moving object
		id_end - ID of the object's destination

		"""
		start_node = self.nodes[id_start]
		end_node = self.nodes[id_end]
		manual_object = self.sceneManager.createManualObject("line%i" % self.lines)
		manual_object.setQueryFlags(self.parent.UNSELECTABLE)
		scene_node = self.rootNode.createChildSceneNode("line%i_node" % self.lines)

		material = ogre.MaterialManager.getSingleton().create("line%i_material" % self.lines, "default")
		material.setReceiveShadows(False)
		material.getTechnique(0).getPass(0).setSelfIllumination(0, 1, 0)

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
		for icon in self.icons.values():
			icon.destroy()
		self.overlays = {}
		self.icons = {}

	def clearObjects(self):
		sm = self.sceneManager
		for oid in self.nodes:
			sm.destroyEntity("Object%i" % oid)
			sm.destroySceneNode("Object%i_Node" % oid)
			sm.destroySceneNode("Object%i_EntityNode" % oid)
			if sm.hasSceneNode("Object%i_Target" % oid):
				sm.destroySceneNode("Object%i_Target" % oid)
			if sm.hasLight("Object%i_Light" % oid):
				sm.destroyLight("Object%i_Light" % oid)
		mm = ogre.MaterialManager.getSingleton()
		for material in self.fleet_colours:
			mm.remove(material)

		#self.rootNode.removeAndDestroyAllChildren()
		self.flareBillboard.clear()
		self.nodes = {}
		self.planets = []
		self.fleets = []
		self.stars = []

	def autofit(self, evt=None):
		"""Zooms out until all stars are visible"""
		fit = False
		self.center()
		camera = self.sceneManager.getCamera("PlayerCam")
		camera_node = self.sceneManager.getSceneNode("CameraNode")
		camera_node.position = ogre.Vector3(0, 0, 0)
		while not fit:
			camera_node.translate(0, 0, 1000)
			self.updateZoom()

			fit = True
			for obj in self.nodes.values():
				if not camera.isVisible(obj.position):
					fit = False
		self.setIconView(False)
		self.max_zoom_out = self.zoom_level
		self.sceneManager.getSceneNode("CameraTarget").position = camera_node.position

	def center(self, id=None):
		"""Center on an object identified by object id, or center on map if id is None"""
		if id:
			node = self.nodes[id]
			pos = node.getPosition()
			cam_focus = self.sceneManager.getSceneNode("CameraFocus")
			cam_focus.position = ogre.Vector3(pos.x, pos.y, 0)
		else:
			map_width = self.map_upper_right[0] - self.map_lower_left[0]
			map_height = self.map_upper_right[1] - self.map_lower_left[1]
			cam_focus = self.sceneManager.getSceneNode("CameraFocus")
			cam_focus.resetOrientation()
			self.h_angle = 0
			self.v_angle = 0
			x = self.map_upper_right[0] - (map_width / 2)
			y = self.map_upper_right[1] - (map_height / 2)
			cam_focus.position = ogre.Vector3(x, y, 0)

	def updateZoom(self):
		camera_node = self.sceneManager.getSceneNode("CameraNode")
		self.zoom_level = -round(camera_node.position.z / 1000)

	def zoom(self, amount):
		"""Zoom in or out for a set amount. Negative amounts will zoom in."""
		target = self.sceneManager.getSceneNode("CameraTarget")
		current = target.position
		z = current.z
		max_zoom = -self.max_zoom_out * 1000
		min_zoom = -self.min_zoom_in * 1000
		if ((z < max_zoom or amount < 0) and (z > min_zoom or amount > 0)):
			if (amount > 0) and (z + amount > max_zoom):
				current.z = max_zoom
				target.setPosition(current)
			elif (amount < 0) and (z + amount < min_zoom):
				current.z = min_zoom
				target.setPosition(current)
			else:
				target.translate(0, 0, amount)

	def zoomIn(self, evt=None):
		self.zoom(-self.default_zoom)
		target = self.sceneManager.getSceneNode("CameraTarget")
		camera = self.sceneManager.getSceneNode("CameraNode")
		camera.setPosition(target.position)
		self.updateZoom()

	def zoomOut(self, evt=None):
		self.zoom(self.default_zoom)
		target = self.sceneManager.getSceneNode("CameraTarget")
		camera = self.sceneManager.getSceneNode("CameraNode")
		camera.setPosition(target.position)
		self.updateZoom()

	def pan(self, x, y):
		cam_focus = self.sceneManager.getSceneNode("CameraFocus")
		cam_focus.translate(x, y, 0, ogre.SceneNode.TransformSpace.TS_LOCAL)
		cam = self.sceneManager.getSceneNode("CameraNode")
		hybrid_position = [cam_focus.position.x, cam_focus.position.y, cam.position.z + abs(cam_focus.position.z)]
		if self.bounding_box != None and not self.bounding_box.intersects(hybrid_position):
			cam_focus.translate(-x, -y, 0, ogre.SceneNode.TransformSpace.TS_LOCAL)
		print cam.position, cam_focus.position, hybrid_position

	def rotate(self, h_angle, v_angle):
		cam_focus = self.sceneManager.getSceneNode("CameraFocus")
		self.v_angle += v_angle
		self.h_angle += h_angle
		q = ogre.Quaternion(ogre.Degree(self.h_angle), ogre.Vector3.UNIT_Z)
		r = ogre.Quaternion(ogre.Degree(self.v_angle), ogre.Vector3.UNIT_X)
		q = q * r
		cam_focus.setOrientation(q)

