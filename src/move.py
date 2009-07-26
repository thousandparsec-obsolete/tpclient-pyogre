import copy

import ogre.renderer.OGRE as ogre

class Participant(ogre.UserDefinedObject):
	""" Basic information is stored here for moving """

	def __init__(self, entity, speed=50.0):
		ogre.UserDefinedObject.__init__(self)
		self.speed = float(speed)
		self.movelist = []
		self.entity = entity
		self.distance = 0.0
		self.direction = ogre.Vector3().ZERO
		self.location = None
		self.moving = False
		self.drift = False

	def addDest(self, dest):
		""" Takes in a tuple for dest """
		destination = ogre.Vector3(dest[0], dest[1], dest[2])
		self.movelist.insert(0, destination)

	def nextDest(self):
		sceneNode = self.entity.getParentSceneNode()
		if not self.location:
			self.location = sceneNode._getDerivedPosition()
		try:
			self.location = self.movelist.pop()
			self.moving = True
			self.setDest(self.location)
			return True
		except IndexError:
			""" Check if perhaps the ship is away from its intended location, set that as a destination if so """
			position = sceneNode._getDerivedPosition()
			if position != self.location:
				self.setDest(self.location)
				self.drift = True
			return False

	def setDest(self, dest):
		sceneNode = self.entity.getParentSceneNode()
		self.direction = self.location - sceneNode._getDerivedPosition()
		if self.moving:
			sceneNode.lookAt(self.location, ogre.SceneNode.TransformSpace.TS_WORLD, ogre.Vector3().UNIT_Z)
		self.distance = self.direction.normalise()

class MoveFrameListener(ogre.FrameListener):
	""" Takes care of moving the ships """

	def __init__(self):
		ogre.FrameListener.__init__(self)
		self.entities = []

	def registerEntity(self, entity, sceneNode):
		if not (entity, sceneNode) in self.entities:
			self.entities.append((entity, sceneNode))

	def frameStarted(self, evt):
		for (entity, sceneNode) in self.entities:
			userObject = entity.getUserObject()
			if userObject.direction == ogre.Vector3().ZERO:
				userObject.nextDest()
			else:
				parentNode = sceneNode.getParentSceneNode()
				move = userObject.speed * evt.timeSinceLastFrame
				userObject.distance -= move
				if userObject.distance < 0.0:
					sceneNode.setPosition(parentNode._getDerivedOrientation().Inverse() * (userObject.location - parentNode._getDerivedPosition()))
					userObject.direction = ogre.Vector3().ZERO
					userObject.moving = False
					userObject.drift = False
				else:
					sceneNode.translate(userObject.direction * move)

		collisions = self.get_collisions()
		for (ent_one, ent_two) in collisions:
			ent_one_object = ent_one.getUserObject()
			self.bounce(ent_one, ent_two)
		return ogre.FrameListener.frameStarted(self, evt)

	def get_collisions(self):
		""" Gets a list of collisions """
		temp_entities = copy.copy(self.entities)
		collisions = []
		for (entity, entity_node) in self.entities:
			temp_entities.pop(0)
			sphere_one = entity.getWorldBoundingSphere(True)
			position_one = entity_node._getDerivedPosition()
			for (ent_two, ent_two_node) in temp_entities:
				sphere_two = ent_two.getWorldBoundingSphere(True)
				if sphere_one.intersects(sphere_two):
					ent_one_object = entity.getUserObject()
					ent_two_object = ent_two.getUserObject()
					# Put the highest priority object first in the order:
					# Moving, non-drifting
					# Moving, drifting
					# Not moving
					# Actually, just moving -> not moving
					if ent_two_object.moving:
						collisions.insert(0, (ent_two, entity))
					else:
						collisions.insert(0, (entity, ent_two))
					entity_node.showBoundingBox(True)
					ent_two_node.showBoundingBox(True)
		return collisions

	def bounce(self, e_one, e_two):
		""" Bounces the two entities apart """
		# Be sure to reset distance if the item is already drifting/otherwise moving and it's bounced
		spheres = (e_one.getWorldBoundingSphere(True), e_two.getWorldBoundingSphere(True))
		parent_nodes = (e_one.getParentSceneNode(), e_two.getParentSceneNode())
		positions = (parent_nodes[0]._getDerivedPosition(), parent_nodes[1]._getDerivedPosition())
		collision_distance = abs(spheres[0].radius+spheres[1].radius - positions[0].distance(positions[1]))
		user_objects = (e_one.getUserObject(), e_two.getUserObject())
		vector = positions[0] - positions[1]
		vector = vector.reflect(positions[0])
		vector.normalise()
		print "%s" % str(vector)
		if user_objects[0].moving and user_objects[1].moving:
			if user_objects[0].drifting and user_objects[1].drifting:
				# Both repel a bit
				parent_nodes[0].translate(-collision_distance/2 * vector)
				parent_nodes[1].translate(collision_distance/2 * vector)
			elif user_objects[0].drifting and not user_objects[1].drifting:
				# Second pushes the first out of the way
				parent_nodes[0].translate(-collision_distance * vector)
			elif not user_objects[0].drifting and user_objects[1].drifting:
				# First pushes the second out of the way
				parent_nodes[1].translate(collision_distance * vector)

			# If neither are drifting then both are moving by direct move event and nothing should happen
		if user_objects[0].moving and not user_objects[1].moving:
			# The first pushes the second out of the way
			parent_nodes[1].translate(collision_distance * vector)
		else:
			# Neither are moving if e_one isn't
			# In this case we bump both a little
			parent_nodes[0].translate(-collision_distance/2 * vector)
			parent_nodes[1].translate(collision_distance/2 * vector)

		self.reset_dist(e_one)
		self.reset_dist(e_two)
		print "Distance collided: %s" % collision_distance

	def reset_dist(self, entity):
		sceneNode = entity.getParentSceneNode()
		user_object = entity.getUserObject()
		location = user_object.location
		user_object.direction = location - sceneNode._getDerivedPosition()
		user_object.distance = user_object.direction.normalise()

