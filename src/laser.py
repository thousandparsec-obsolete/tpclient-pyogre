import ogre.renderer.OGRE as ogre

class Laser:

	def __init__(self, sceneManager, material_name):
		self.laser = sceneManager.createBillboardChain("Laser")
		self.laser.materialName = material_name
		self.sceneManager = sceneManager
		self.laser.maxChainElements = 2
		lasernode = self.sceneManager.getRootSceneNode().createChildSceneNode()
		lasernode.attachObject(self.laser)

	def fire(self, source, target):
		""" Takes in two SceneNodes and puts a laser up between them """
		self.laser.addChainElement(0, ogre.BillboardChain.Element(source._getDerivedPosition(), 10, 0.0, ogre.ColourValue(1.0, 1.0, 1.0)))
		self.laser.addChainElement(0, ogre.BillboardChain.Element(target._getDerivedPosition(), .1, 1.0, ogre.ColourValue(1.0, 1.0, 1.0)))
		self.laser.setVisible(True)

	def destroy(self):
		self.laser.getParentSceneNode().detachObject(self.laser)
		self.sceneManager.destroyBillboardChain(self.laser)
		self.laser = None

