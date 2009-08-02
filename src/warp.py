import copy

import ogre.renderer.OGRE as ogre

class WarpFrameListener(ogre.FrameListener):
	""" Takes care of moving the ships """

	def __init__(self, sceneManager):
		ogre.FrameListener.__init__(self)
		self.entities = []
		self.warp_lock = True
		self.warped = 0
		self.sceneManager = sceneManager
		self.warptimer = ogre.Timer()

	def registerEntity(self, entity, sceneNode):
		if not (entity, sceneNode) in self.entities:
			battle_entity = entity.getUserObject().battle_entity
			warp_particles = self.sceneManager.createParticleSystem(battle_entity.name + "/Warp", "Warp")
			sceneNode.attachObject(warp_particles)
			self.entities.append((entity, sceneNode, warp_particles))

	def frameStarted(self, evt):
		# If everyone has been warped in
		if not self.warp_lock:
			return ogre.FrameListener.frameStarted(self, evt)

		if self.warped == len(self.entities):
			time = self.warptimer.getMilliseconds()
			if time > 1000:
				for (entity, sceneNode, warp_particles) in self.entities:
					warp_particles.setVisible(False)
					warp_particles.detatchFromParent()
				self.entities = []
				self.warped = 0
				self.warp_lock = False
			return ogre.FrameListener.frameStarted(self, evt)

		for (entity, sceneNode, warp_particles) in self.entities:
			if warp_particles.getNumParticles() == warp_particles.getParticleQuota():
				entity.setVisible(True)
				# detatch typo is in ogre
				self.warped += 1
				self.warptimer.reset()


		return ogre.FrameListener.frameStarted(self, evt)
