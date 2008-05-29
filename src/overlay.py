import ogre.renderer.OGRE as ogre

class ObjectOverlay(object):
	def __init__(self, node, object):
		self.node = node
		self.entity = "Object%i" % object.id
		self.active = []

		overlayManager = ogre.OverlayManager.getSingleton()
		panel = overlayManager.createOverlayElement("Panel", "Panel%i" % object.id)
		panel.metricsMode = ogre.GMM_PIXELS
		# FIXME: This should be calculated...
		panel.dimensions = (100, 100)
		self.panel = panel
	
		name = overlayManager.createOverlayElement("TextArea", "Name%i" % object.id)
		name.metricsMode = ogre.GMM_PIXELS
		name.charHeight = 16
		name.fontName = "Tahoma-12"
		name.caption = object.name
		self.name = name

		#position = overlayManager.createOverlayElement("TextArea", "Position%i" % object.id)
		#position.metricsMode = ogre.GMM_PIXELS
		#position.setPosition(0, 16)
		#position.charHeight = 16
		#position.fontName = "Tahoma-12"
		#position.caption = "%i, %i, %i" % object.pos
		#self.position = position

		self.overlay = overlayManager.create("Overlay%i" % object.id)
		self.overlay.add2D(self.panel)

		# WARN: This needs to happen after the panel is added to an overlay
		panel.addChild(name)
		#panel.addChild(position)

	def show(self, *which):
		for text in self.active:
			text.hide()

		self.active = which

		for text in self.active:
			text.show()

	def update(self, camera):
		entity = self.node.getAttachedObject(0)
	
		#pos = self.node.worldPosition
		pos =  self.node._getWorldAABB().getMaximum()
		pos = camera.viewMatrix*pos
		pos = camera.projectionMatrix*pos
	
		if abs(pos[0]) < 1 and abs(pos[1]) < 1 and pos[2] < 1 and entity.visible:
			if not self.overlay.isVisible():
				self.overlay.show()

			pos /= 2

			pos = ((0.5 + pos.x)*(camera.viewport.actualWidth), (0.5 - pos.y)*camera.viewport.actualHeight)
			self.panel.setPosition(pos[0], pos[1])
		else:
			if self.overlay.isVisible():
				self.overlay.hide()

	def setColour(self, ColourValue):
		#for overlay in (self.name, self.position):
			#overlay.colour = ColourValue
		self.name.colour = ColourValue

	def getColour(self):
		return self.name.ColourValue
	colour = property(getColour, setColour)


