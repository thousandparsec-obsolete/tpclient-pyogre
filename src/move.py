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
				else:
					sceneNode.translate(userObject.direction * move)

		collisions = self.get_collisions()
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
					collisions.insert(0, (entity, ent_two))
					entity_node.showBoundingBox(True)
					ent_two_node.showBoundingBox(True)
		return collisions

	def bounce(self, e_mover, e_obstacle):
		""" Bounces the two entities apart """
		# Be sure to reset distance if the item is already drifting/otherwise moving and it's bounced
		spheres = (e_mover.getWorldBoundingSphere(True), e_obstacle.getWorldBoundingSphere(True))
		parent_nodes = (e_mover.getParentSceneNode(), e_obstacle.getParentSceneNode())
		positions = (parent_nodes[0]._getDerivedPosition(), parent_nodes[1]._getDerivedPosition())
		collision_distance = abs(spheres[0].radius+spheres[1].radius - positions[0].distance(positions[1]))
		vector = positions[0] - positions[1]
		vector = vector.reflect(positions[0])
		vector.normalise()
		print "%s" % str(vector)
		# Mover moves
		# Negative collision_distance, because the vector is pointing towards the obstacle
#		parent_nodes[0].translate(collision_distance * vector)
		# Obstacle moves
		parent_nodes[1].translate(collision_distance * vector)
		# Both move
#		parent_nodes[0].translate(-collision_distance/2 * vector)
#		parent_nodes[1].translate(collision_distance/2 * vector)
		print "Distance collided: %s" % collision_distance

