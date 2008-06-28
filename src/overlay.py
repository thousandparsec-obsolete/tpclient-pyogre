import math

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

import helpers

class IconOverlay(object):
	# FIXME: Repetition with ObjectOverlay

	def __init__(self, node, object, material, width=25, height=25, colour=ogre.ColourValue.White):
		self.node = node
		self.original_material = material
		self.highlight = False

		overlayManager = ogre.OverlayManager.getSingleton()
		panel = overlayManager.createOverlayElement("Panel", "Panel_Icon_%i" % object.id)
		panel.metricsMode = ogre.GMM_PIXELS
		panel.width = width
		panel.height = height
		panel.materialName = material
		self.panel = panel

		self.overlay = overlayManager.create("Overlay%i_Icon" % object.id)
		self.overlay.add2D(self.panel)
		self.overlay.show()

	def setHighlight(self, highlight, colour=ogre.ColourValue.White):
		material = self.panel.material
		clone_material_name = "%s_highlight" % self.original_material
		material_manager = ogre.MaterialManager.getSingleton()
		if highlight:
			if material_manager.resourceExists(clone_material_name):
				material_clone = material_manager.getByName(clone_material_name)
			else:
				material_clone = material.clone(clone_material_name)
				texture = material_clone.getTechnique(0).getPass(0).getTextureUnitState(0)
				texture.setColourOperationEx(ogre.LBX_MODULATE_X4, ogre.LBS_TEXTURE, ogre.LBS_MANUAL, colour)
			self.panel.materialName = material_clone.name
		else:
			self.panel.materialName = self.original_material
			material_manager.remove(material)
		self.highlight = highlight

	def setVisible(self, visible):
		if visible:
			self.panel.show()
		else:
			self.panel.hide()

	def update(self, camera):
		entity = self.node.getAttachedObject(0)
	
		pos =  self.node._getWorldAABB().getMaximum()
		pos = camera.viewMatrix*pos
		pos = camera.projectionMatrix*pos

		offset_x = -20
		offset_y = -5
	
		if abs(pos[0]) < 1 and abs(pos[1]) < 1 and pos[2] < 1:
			if not self.overlay.isVisible():
				self.overlay.show()

			pos /= 2

			pos = ((0.5 + pos.x)*(camera.viewport.actualWidth) + offset_x, (0.5 - pos.y)*camera.viewport.actualHeight + offset_y)
			self.panel.setPosition(pos[0], pos[1])
		else:
			if self.overlay.isVisible():
				self.overlay.hide()

class ObjectOverlay(object):
	def __init__(self, node, object):
		self.node = node
		self.entity = "Object%i" % object.id
		self.active = []

		overlayManager = ogre.OverlayManager.getSingleton()
		panel = overlayManager.createOverlayElement("Panel", "Panel%i" % object.id)
		panel.metricsMode = ogre.GMM_PIXELS
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

	def destroy(self):
		"""Destroy and remove this overlay"""
		overlayManager = ogre.OverlayManager.getSingleton()
		overlayManager.destroyOverlayElement(self.name)
		overlayManager.destroyOverlayElement(self.panel)
		overlayManager.destroy(self.overlay)

	def show(self, *which):
		for text in self.active:
			text.hide()

		self.active = which

		for text in self.active:
			text.show()

	def setVisible(self, visible):
		if visible:
			self.panel.show()
		else:
			self.panel.hide()

	def update(self, camera):
		entity = self.node.getAttachedObject(0)
	
		#pos = self.node.worldPosition
		pos =  self.node._getWorldAABB().getMaximum()
		pos = camera.viewMatrix*pos
		pos = camera.projectionMatrix*pos

		offset_x = 10
		offset_y = 0
	
		if abs(pos[0]) < 1 and abs(pos[1]) < 1 and pos[2] < 1:
			if not self.overlay.isVisible():
				self.overlay.show()

			pos /= 2

			pos = ((0.5 + pos.x)*(camera.viewport.actualWidth) + offset_x, (0.5 - pos.y)*camera.viewport.actualHeight + offset_y)
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

class RadialMenu(object):
	def __init__(self, camera):
		self.camera = camera
		self.buttons = []

		image = cegui.ImagesetManager.getSingleton().createImagesetFromImageFile("Radial", "halo2.png")

		wm = cegui.WindowManager.getSingleton()
		self.menu = wm.createWindow("SleekSpace/StaticImage", "RadialMenu")
		self.menu.size = cegui.UVector2(cegui.UDim(0.23, 0), cegui.UDim(0.3, 0))
		self.menu.setProperty("Image", "set:Radial image:full_image")
		self.menu.hide()

	def add(self, caption, parent, handler):
		wm = cegui.WindowManager.getSingleton()
		index = len(self.buttons)
		button = wm.createWindow("SleekSpace/Button", "RadialMenu/Button%i" % index)
		button.size = cegui.UVector2(cegui.UDim(0.5, 0), cegui.UDim(0.2, 0))
		button.text = caption
		button.setProperty("ClippedByParent", "False")
		self.menu.addChildWindow(button)
		self.buttons.append(button)
		self.arrange()
		helpers.bindEvent("RadialMenu/Button%i" % index, parent, handler, cegui.PushButton.EventClicked)

	def clear(self):
		wm = cegui.WindowManager.getSingleton()
		for button in self.buttons:
			self.menu.removeChildWindow(button)
			wm.destroyWindow(button)
		self.buttons = []

	def arrange(self):
		i = 1
		spacing = 360 / len(self.buttons)
		for button in self.buttons:
			position = [0.5, 0.5]
			interval = spacing * i
			interval = math.radians(interval)
			x = 0.5 * math.cos(interval)
			y = 0.5 * math.sin(interval)
			position[0] += x
			position[1] += y
			i += 1
			button.position = cegui.UVector2(cegui.UDim(position[0] - 0.25, 0), cegui.UDim(position[1] - 0.05, 0))

	def toggle(self):
		if self.menu.isVisible():
			self.close()
			return False
		else:
			self.open()
			return True

	def close(self):
		self.clear()
		self.menu.hide()

	def open(self):
		if not self.entity:
			return

		bbox = self.entity.getWorldBoundingBox(True)
		corners = bbox.getAllCorners()
		min = [1, 1]

		for corner in corners:
			corner = self.camera.viewMatrix * corner
			x = corner.x / corner.z + 0.5
			y = corner.y / corner.z + 0.5
			x = 1 - x
			if (x < min[0]):
				min[0] = x
			if (y < min[1]):
				min[1] = y

		if min[0] < 0:
			min[0] = 0
		if min[1] < 0:
			min[1] = 0

		self.menu.show()
		manager = ogre.OverlayManager.getSingleton()
		self.update(manager.viewportWidth * min[0], manager.viewportHeight * min[1])

	def update(self, x, y):
		self.menu.position = cegui.UVector2(cegui.UDim(-0.10, x), cegui.UDim(-0.12, y))

