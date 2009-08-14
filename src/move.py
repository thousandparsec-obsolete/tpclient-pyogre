import copy

import ogre.renderer.OGRE as ogre

class MoveFrameListener(ogre.FrameListener):
	""" Takes care of moving the ships """

	def __init__(self):
		ogre.FrameListener.__init__(self)
		self.entities = []

	def registerEntity(self, entity, sceneNode):
		if not (entity, sceneNode) in self.entities:
			self.entities.append((entity, sceneNode))

	def move_lock(self):
		""" Checks if any entity is moving, if so, returns True """
		# remember to execute this when checking for locks
		lock = False
		for (entity, sceneNode) in self.entities:
			userObject = entity.getUserObject()
			lock = lock or (userObject.moving and not userObject.drift)
		return lock

	def frameStarted(self, evt):
		for (entity, sceneNode) in self.entities:
			userObject = entity.getUserObject()
			if userObject.direction == ogre.Vector3().ZERO or userObject.drift:
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
					if userObject.engine_particles:
						for i in range(0, userObject.engine_particles.getNumEmitters()):
							userObject.engine_particles.getEmitter(i).setEnabled(False)
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
		if user_objects[0].moving and user_objects[1].moving:
			if user_objects[0].drift and user_objects[1].drift:
				# Both repel a bit
				parent_nodes[0].translate(-collision_distance/2 * vector)
				parent_nodes[1].translate(collision_distance/2 * vector)
			elif user_objects[0].drift and not user_objects[1].drift:
				# Second pushes the first out of the way
				parent_nodes[0].translate(-collision_distance * vector)
			elif not user_objects[0].drift and user_objects[1].drift:
				# First pushes the second out of the way
				parent_nodes[1].translate(collision_distance * vector)

			# If neither are drifting then both are moving by direct move event and nothing should happen
		if user_objects[0].moving and not user_objects[1].moving:
			# The first pushes the second out of the way
			parent_nodes[1].translate(collision_distance * vector)
		else:
			# Neither are moving if e_one isn't
			# In this case we bump both a little
			parent_nodes[0].translate(-collision_distance/3 * vector)
			parent_nodes[1].translate(collision_distance*2/3 * vector)

		self.reset_dist(e_one)
		self.reset_dist(e_two)

	def reset_dist(self, entity):
		sceneNode = entity.getParentSceneNode()
		user_object = entity.getUserObject()
		location = user_object.location
		user_object.direction = location - sceneNode._getDerivedPosition()
		user_object.distance = user_object.direction.normalise()

