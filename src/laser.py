import ogre.renderer.OGRE as ogre

from raycast import raycastFromPoint

class LaserManager:

	def __init__(self, sceneManager, material_name):
		self.lasers = []
		self.sceneManager = sceneManager
		self.material_name = material_name
		self.num = 0

	def batch_fire(self, fire_pairs):
		for (source, target) in fire_pairs:
			self.fire(source, target)

	def fire(self, source, target):
		available = None
		for i in range(len(self.lasers)):
			if not self.lasers[i].laser.isVisible():
				available = i
				break
		if not available:
			self.lasers.append(Laser(self.sceneManager, self.material_name, self.name()))
			i = len(self.lasers)-1

		self.lasers[i].fire(source,target)

	def name(self):
		self.num += 1
		return self.num

	def clear(self):
		for i in self.lasers:
			i.stop()

	def destroy(self):
		for i in self.lasers:
			i.destroy()


class Laser:

	def __init__(self, sceneManager, material_name, name):
		self.laser = sceneManager.createBillboardChain("Laser_%d" % name)
		self.laser.materialName = material_name
		self.sceneManager = sceneManager
		self.laser.maxChainElements = 2
		lasernode = self.sceneManager.getRootSceneNode().createChildSceneNode()
		lasernode.attachObject(self.laser)
		self.particles = self.sceneManager.createParticleSystem("Laser_%d_particles" % name,"Fire/Laser")

	def fire(self, source, target):
		""" Takes in two SceneNodes and puts a laser up between them """
		self.laser.addChainElement(0, ogre.BillboardChain.Element(source._getDerivedPosition(), 10, 0.0, ogre.ColourValue(1.0, 1.0, 1.0)))
		self.laser.addChainElement(0, ogre.BillboardChain.Element(target._getDerivedPosition(), .1, 1.0, ogre.ColourValue(1.0, 1.0, 1.0)))
		self.laser.setVisible(True)
		target.attachObject(self.particles)

	def stop(self):
		self.laser.setVisible(False)
		self.particles.detatchFromParent()

	def destroy(self):
		self.laser.getParentSceneNode().detachObject(self.laser)
		self.sceneManager.destroyBillboardChain(self.laser)
		self.laser = None

