import ogre.renderer.OGRE as ogre


class Torpedo(object):
	""" Creates the torpedo weapon """

	def __init__(self, sceneManager):
		self.sceneNode = sceneManager.getRootSceneNode().createChildSceneNode("Torpedo")
		self.sceneNode.setVisible(False)
		self.torpedo = sceneManager.createParticleSystem("Torpedo_Particle", "Gun")
		self.sceneNode.attachObject(self.torpedo)
		self.torpedo.setKeepParticlesInLocalSpace(True)
		self.bulletTimer = ogre.Timer()
		self.fired = False
		self.eta = 0

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
		# +1 is for the extra time it might take to get to the center of the scene node, for some reason the torpedo stops at the AABB of the model :\
		time = distance/velocity+1
		emitter.setTimeToLive(time)
		emitter.setTimeToLive(time, time)
#		planeDeflector = self.torpedo.getAffector(0)
#		planeDeflector.setParameter("plane_normal", "%d %d %d" % (normal.x, normal.y, normal.z))
#		planeDeflector.setParameter("plane_point", " %d %d %d" % (target.x, target.y, target.z))
		emitter.setEnabled(True)
		emitted_emitter = self.torpedo.getEmitter(1)
		emitted_emitter.setEnabled(True)
		self.fired = True
		self.eta = time
		self.bulletTimer.reset()

	def torpedo_lock(self):
		if self.bulletTimer.getMilliseconds() < 1000*self.eta:
			return True
		return False

	def clear(self):
		self.eta = 0
		self.fired = False
		emitter = self.torpedo.getEmitter(0)
		emitted_emitter = self.torpedo.getEmitter(1)
		self.sceneNode.setVisible(False)
