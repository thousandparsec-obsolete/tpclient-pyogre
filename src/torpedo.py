import ogre.renderer.OGRE as ogre

class Torpedo(object):
	""" Creates the torpedo weapon """

	def __init__(self, sceneManager):
		self.sceneNode = sceneManager.getRootSceneNode().createChildSceneNode("Torpedo")
		self.torpedo = sceneManager.createParticleSystem("Torpedo_Particle", "Gun")
		self.sceneNode.attachObject(self.torpedo)
		self.torpedo.setKeepParticlesInLocalSpace(True)

	def fire(self, source, target):
		source = source._getDerivedPosition()
		target = target._getDerivedPosition()
		self.sceneNode.setVisible(True)
		self.sceneNode.setPosition(source)
		self.sceneNode.lookAt(target, ogre.SceneNode.TransformSpace.TS_WORLD, ogre.Vector3().UNIT_Z)
		normal = target - source
		normal.normalise()
		distance = abs(target.distance(source))
		emitter = self.torpedo.getEmitter(0)
		velocity = emitter.getParticleVelocity()
		time = distance/velocity
		emitter.setTimeToLive(time)
		emitter.setTimeToLive(time, time)
#		planeDeflector = self.torpedo.getAffector(0)
#		planeDeflector.setParameter("plane_normal", "%d %d %d" % (normal.x, normal.y, normal.z))
#		planeDeflector.setParameter("plane_point", " %d %d %d" % (target.x, target.y, target.z))
		emitter.setEnabled(True)
		emitted_emitter = self.torpedo.getEmitter(1)

		emitted_emitter.setEnabled(True)

	def clear(self):
		self.sceneNode.setVisible(False)
