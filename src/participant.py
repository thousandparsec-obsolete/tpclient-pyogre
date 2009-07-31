import ogre.renderer.OGRE as ogre

from overlay import ObjectOverlay

class Participant(ogre.UserDefinedObject):
	""" Basic information is stored here for moving """

	def __init__(self, entity, battle_entity, speed=50.0):
		ogre.UserDefinedObject.__init__(self)
		self.speed = float(speed)
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

