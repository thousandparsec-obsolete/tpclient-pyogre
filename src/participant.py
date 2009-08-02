import ogre.renderer.OGRE as ogre

from overlay import ObjectOverlay

class Participant(ogre.UserDefinedObject):
	""" Basic information is stored here for moving """

	def __init__(self, entity, battle_entity, **kwargs):
		ogre.UserDefinedObject.__init__(self)
		if kwargs.has_key('speed'):
			self.speed = float(kwargs['speed'])
		else:
			self.speed = 50.0

		if kwargs.has_key('engine'):
			self.engine_particles = kwargs['engine']
			self.engine_particles.setVisible(False)
		else:
			self.engine_particles = None

		self.movelist = []
		self.entity = entity
		self.battle_entity = battle_entity
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
		try:
			self.location = self.movelist.pop()
			self.moving = True
			self.setDest(self.location)
			self.engine_particles.setVisible(True)
			return True
		except IndexError:
			""" Check if perhaps the ship is away from its intended location, set that as a destination if so """
			position = sceneNode._getDerivedPosition()
			if position != self.location:
				self.setDest(self.location)
				self.drift = True
			return False
		if not self.location:
			self.location = sceneNode._getDerivedPosition()

	def setDest(self, dest):
		sceneNode = self.entity.getParentSceneNode()
		self.direction = self.location - sceneNode._getDerivedPosition()
		if self.moving:
			sceneNode.lookAt(self.location, ogre.SceneNode.TransformSpace.TS_WORLD, ogre.Vector3().UNIT_Z)
		self.distance = self.direction.normalise()

