import math
import ogre.renderer.OGRE as ogre

class MovableText(ogre.MovableObject, ogre.Renderable): 
	POS_TEX_BINDING = 0
	COLOUR_BINDING = 1
	
	def __init__(self, name, caption, fontName="Tahoma-12", color=ogre.ColourValue.White):
		self.name = name
		self.caption = caption
		self.fontName = fontName
		self.color = color

		self.camera = None
		self.window = None

		self.renderOp.vertexData = None
		self.type = "MovableText"
		self.spaceWidth = 0
		self.updateColors = True;
		self.onTop = True;
		
		self.setupGeometry()

		self._font = None
		self._material = None
		self._needUpdate = True

	def setFontName(self, fontName):
		self._fontName = fontName
		self._font = ogre.FontManager.getSingleton().getByName(fontName);
		if self._font is None:
			raise ogre.Exception(ogre.Exception.ERR_ITEM_NOT_FOUND, "Could not find font " + fontName)

		self._font.load()
		
		self._material = self._font.material.clone(self.name + "Material");
		if not self._material.isLoaded():
			self._material.load()
		self._material.setDepthCheckEnabled(not self.onTop)
		self._material.setLightingEnabled(False)
		self._needUpdate = True
		
	def getFontName(self):
		return self._fontName
	fontName = property(getFontName, setFontName)
	
	def setOnTop(self, show):
		self._onTop = show
		if self._material:
			self._material.setDepthBias(self._onTop)
	
	def getOnTop(self):
		return self._onTop
	onTop = property(getOnTop, setOnTop)

	def setName(self, name):
		self._name = name

	def getName(self):
		return self._name
	name = property(getName, setName)

	def setSpaceWidth(self, width):
		self._needUpdate = True
		self._spaceWidth = width
	
	def getSpaceWidth(self):
		return self._spaceWidth
	spaceWidth = property(getSpaceWidth, setSpaceWidth)

	def setCaption(self, caption):
		self._needUpdate = True
		self._caption = caption
	
	def getCaption(self):
		return self._caption
	caption = property(getCaption, setCaption)

	def setColour(self, colour):
		self._needUpdate = True
		self._colour = colour
	
	def getColour(self):
		return self._colour
	colour = property(getColour, setColour)

	def setCharacterHeight(self, characterHeight):
		self._needUpdate = True
		self._characterHeight = characterHeight
	
	def getCharacterHeight(self):
		return self._characterHeight
	characterHeight = property(getCharacterHeight, setCharacterHeight)

	def _setupGeometry(self):
		vertexCount = len(self.caption) * 6;
	
		if self.renderOp.vertexData is not None:
			if self.renderOp.vertexData.vertexCount != vertexCount:
				self.renderOp.vertexData = None
	
				self._updateColors = True
	
		if self.renderOp.vertexData is None:
			self.renderOp.vertexData = ogre.VertexData()

		self.renderOp.indexData = 0
		self.renderOp.vertexData.vertexStart = 0
		self.renderOp.vertexData.vertexCount = vertexCount
		self.renderOp.operationType = ogre.RenderOperation.OT_TRIANGLE_LIST
		self.renderOp.useIndexes = False

		decl = self.renderOp.vertexData.vertexDeclaration
		bind = self.renderOp.vertexData.vertexBufferBinding
		
		offset = 0
		decl.addElement(POS_TEX_BINDING, offset, Ogre.VET_FLOAT3, Ogre.VES_POSITION)
		offset += VertexElement.getTypeSize(VET_FLOAT3)
		
		decl.addElement(POS_TEX_BINDING, offset, Ogre.VET_FLOAT2, Ogre.VES_TEXTURE_COORDINATES, 0)
		
		ptbuf = ogre.HardwareBufferManager.getSingleton().createVertexBuffer(
				decl.getVertexSize(POS_TEX_BINDING),
				self.renderOp.vertexData.vertexCount,
				ogre.HardwareBuffer.HBU_DYNAMIC_WRITE_ONLY)
		bind.setBinding(POS_TEX_BINDING, ptbuf)

		decl.addElement(COLOUR_BINDING, 0, ogre.VET_COLOUR, ogre.VES_DIFFUSE)
		cbuf = ogre.HardwareBufferManager.getSingleton().createVertexBuffer(
				decl.getVertexSize(COLOUR_BINDING),
				mRenderOp.vertexData.vertexCount,
				ogre.HardwareBuffer.HBU_DYNAMIC_WRITE_ONLY)
		bind.setBinding(COLOUR_BINDING, cbuf)

		pPCIndex = 0
		pPCBuff = ptbuf.lock(ogre.HardwareBuffer.HBL_DISCARD)

		if (self.spaceWidth == 0):
			self.spaceWidth = self.font.getGlyphAspectRatio( 'A' )
		
		left = 0.0
		top = 0.0
		width = 0.0
		
		first = True
		newLine = True
		for i in xrange(0, len(self.caption)):
			if newLine:
				width = 0.0

				j = i
				while j < len(self.caption) and self.caption[j] != '\n':
					if self.caption[j] == ' ':
						width += self.spaceWidth
					else:
						width += self.font.getGlyphAspectRation(self.caption[j]) * mCharHeight * 2.0
			
				newLine = False
			
			if self.caption[i] == '\n':
				left = 0
				top -= mCharHeight * 2.0
				newLine = True
				continue

			if self.caption[i] == ' ':
				# Just leave a gap, no tris
				left += self.spaceWidth
				# Also reduce tri count
				self.renderOp.vertexData.vertexCount -= 6;
				continue

			horiz_height = self.font.getGlyphAspectRatio( self.caption[i] )
			(u1, v1, u2, v2) = self.font.getGlyphTexCoords( self.caption[i] )

			# each vert is (x, y, z, u, v)
			#-------------------------------------------------------------------------------------
			# First tri
			#
			# Upper left
			pPCBuff.setFloat(pPCIndex, left);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, top);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, -1.0);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, u1);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, v1);		pPCIndex += 1

			# Deal with bounds
			currPos = Ogre.Vector3(left, top, -1.0)
			if first:
				min = max = currPos
				maxSquaredRadius = currPos.squaredLength();
				first = False
			else:
				min.makeFloor(currPos)
				max.makeCeil(currPos)
				maxSquaredRadius = math.max(maxSquaredRadius, currPos.squaredLength())

			top -= mCharHeight * 2.0

			# Bottom left
			pPCBuff.setFloat(pPCIndex, lef);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, top);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, -1.0);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, u1);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, v2);		pPCIndex += 1

			# Deal with bounds
			currPos = Ogre.Vector3(left, top, -1.0)
			min.makeFloor(currPos)
			max.makeCeil(currPos)
			maxSquaredRadius = math.max(maxSquaredRadius, currPos.squaredLength())

			top += mCharHeight * 2.0
			left += horiz_height * mCharHeight * 2.0

			# Top right
			pPCBuff.setFloat(pPCIndex, left);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, top);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, -1.0);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, u2);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, v1);		pPCIndex += 1
			#-------------------------------------------------------------------------------------

			# Deal with bounds
			currPos = Ogre.Vector3(left, top, -1.0)
			min.makeFloor(currPos)
			max.makeCeil(currPos)
			maxSquaredRadius = math.max(maxSquaredRadius, currPos.squaredLength())

			#-------------------------------------------------------------------------------------
			# Second tri
			#
			# Top right (again)
			pPCBuff.setFloat(pPCIndex, left);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, top);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, -1.0);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, u2);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, v1);		pPCIndex += 1

			currPos = Ogre.Vector3(left, top, -1.0)
			min.makeFloor(currPos)
			max.makeCeil(currPos)
			maxSquaredRadius = math.max(maxSquaredRadius, currPos.squaredLength())

			top -= mCharHeight * 2.0
			left -= horiz_height  * mCharHeight * 2.0

			# Bottom left (again)
			pPCBuff.setFloat(pPCIndex, left);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, top);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, -1.0);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, u1);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, v2);		pPCIndex += 1

			currPos = Ogre.Vector3(left, top, -1.0)
			min.makeFloor(currPos)
			max.makeCeil(currPos)
			maxSquaredRadius = math.max(maxSquaredRadius, currPos.squaredLength())

			left += horiz_height  * mCharHeight * 2.0

			# Bottom right
			pPCBuff.setFloat(pPCIndex, left);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, top);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, -1.0);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, u2);		pPCIndex += 1
			pPCBuff.setFloat(pPCIndex, v2);		pPCIndex += 1
			#-------------------------------------------------------------------------------------

			currPos = Ogre.Vector3(left, top, -1.0)
			min.makeFloor(currPos)
			max.makeCeil(currPos)
			maxSquaredRadius = math.max(maxSquaredRadius, currPos.squaredLength())

			# Go back up with top
			top += mCharHeight * 2.0

			currentWidth = (left + 1)/2 - 0
		
		# Unlock vertex buffer
		ptbuf.unlock()

		# update AABB/Sphere radius
		mAABB = Ogre.AxisAlignedBox(min, max)
		mRadius = Ogre.Math.Sqrt(maxSquaredRadius)

		if (self.updateColors):
			self._updateColors()

		self.needUpdate = False
	
	def _updateColors(self):
		# Convert to system-specific
		color = ogre.Root.getSingleton().convertColourValue(self.color)
		
		vbuf = self.renderOp.vertexData.vertexBufferBinding.getBuffer(COLOUR_BINDING)
		pDest = vbuf.lock(ogre.HardwareBuffer.HBL_DISCARD)

		for i in range(0, self.renderOp.vertexData.vertexCount):
			pDest.setFloat(i, color)
		
		vbuf.unlock()
		
		self.updateColors = False

	def getWorldOrientation(self):
		return self.camera._getDerivedOrientation()
		
	def getWorldPosition(self):
		return self.parentNode._getDerivedPosition()

	def getWorldTransforms(self, xform):
		if self.isVisible() and not mpCam is None:
			rot3x3, scale3x3 = ogre.Matrix3.IDENTITY
			# store rotation in a matrix
			self.camera.getDerivedOrientation().ToRotationMatrix(rot3x3)
			
			# parent node position
			ppos = self.parentNode._getDerivedPosition()

			# apply scale
			scale3x3[0][0] = self.parentNode._getDerivedScale().x / 2;
			scale3x3[1][1] = self.parentNode._getDerivedScale().y / 2;
			scale3x3[2][2] = self.parentNode._getDerivedScale().z / 2;
			
			# apply all transforms to xform			
			xform = rot3x3 * scale3x3
			xform.setTrans(ppos)
	
	def getRenderOperation(self):
		if self.isVisible():
			if self.needUpdate:
				self._setupGeometry()
			if self.updateColors:
				self._updateColors()
			
			return self.renderOp
	
	def _notifyCurrentCamera(cam):
		self.camera = cam
	
	def _updateRenderQueue(queue):
		if self.isVisible():
			if self.needUpdate:
				self._setupGeometry()
			if self.updateColors:
				this._updateColors()
			queue.addRenderable(self, self.renderQueueID)

def createSphere(name, radius, rings=16, segments=16):
	sphere = ogre.MeshManager.getSingleton().createManual(name, "Generated")
	sphereVertex = sphere.createSubMesh()
	
	sphere.sharedVertexData = ogre.VertexData()
	vertexData = sphere.sharedVertexData

	# Define the vertex format
	vertexDecl = vertexData.vertexDeclaration
	currentOffset = 0
	
	# Positions
	vertexDecl.addElement(0, currentOffset, ogre.VET_FLOAT3, ogre.VES_POSITION)
	currentOffset += ogre.VertexElement.getTypeSize(ogre.VET_FLOAT3)

	# Normals
	vertexDecl.addElement(0, currentOffset, ogre.VET_FLOAT3, ogre.VES_NORMAL)
	currentOffset += ogre.VertexElement.getTypeSize(ogre.VET_FLOAT3)

	# Two dimensional texture coordinates
	vertexDecl.addElement(0, currentOffset, ogre.VET_FLOAT2, ogre.VES_TEXTURE_COORDINATES, 0)
	currentOffset += ogre.VertexElement.getTypeSize(ogre.VET_FLOAT2)

	# Allocate the vertex buffer
	vertexData.vertexCount = (rings+1)*(segments+1)
	vBuffer = ogre.HardwareBufferManager.getSingleton().createVertexBuffer(
		vertexDecl.getVertexSize(0), vertexData.vertexCount, ogre.HardwareBuffer.HBU_STATIC_WRITE_ONLY, False)

	binding = vertexData.vertexBufferBinding
	binding.setBinding(0, vBuffer)

	vertex = vBuffer.lock(vertexDecl, ogre.HardwareBuffer.HBL_DISCARD)

	sphereVertex.indexData.indexCount = 6*rings*(segments+1)
	sphereVertex.indexData.indexBuffer = ogre.HardwareBufferManager.getSingleton().createIndexBuffer(
		ogre.HardwareIndexBuffer.IT_16BIT, sphereVertex.indexData.indexCount, ogre.HardwareBuffer.HBU_STATIC_WRITE_ONLY, False)
	iBuffer = sphereVertex.indexData.indexBuffer

	indices = iBuffer.lock(vertexDecl, ogre.HardwareBuffer.HBL_DISCARD)
	
	deltaRingAngle = math.pi / rings
	deltaSegAngle = (2* math.pi / segments)

	verticeIndex = 0
	pI = 0

	for ring in xrange(0, rings+1):
		r0 = radius * math.sin(ring * deltaRingAngle)
		y0 = radius * math.cos(ring * deltaRingAngle)

		for seg in xrange(0, segments+1):
			x0 = r0 * math.sin(seg * deltaSegAngle)
			z0 = r0 * math.cos(seg * deltaSegAngle)

			print verticeIndex

			vertex.setFloat(verticeIndex, 0, x0, y0, z0)
			print vertex.getFloat(verticeIndex, 0, 3)

			normal = ogre.Vector3(x0, y0, z0).normalisedCopy()
			vertex.setFloat(verticeIndex, 1, normal.x, normal.y, normal.z)
			print vertex.getFloat(verticeIndex, 1, 3)
			vertex.setFloat(verticeIndex, 2, seg*1.0 / segments, ring*1.0 / rings)
			print vertex.getFloat(verticeIndex, 1, 2)

			print "---------------------"

			if (ring != rings):
				indices[pI] = verticeIndex + segments + 1; pI+=1
				indices[pI] = verticeIndex; pI+=1
				indices[pI] = verticeIndex + segments; pI+=1
				indices[pI] = verticeIndex + segments + 1; pI+=1
				indices[pI] = verticeIndex + 1; pI+=1
				indices[pI] = verticeIndex; pI+=1
				verticeIndex += 1

	vBuffer.unlock()
	iBuffer.unlock()

	sphereVertex.useSharedVertices = True;
	sphere._setBounds( ogre.AxisAlignedBox( 
		ogre.Vector3(-radius, -radius, -radius), ogre.Vector3(-radius, -radius, -radius)), False)
	sphere._setBoundingSphereRadius(radius)
	sphere.load()

def test():
	from Framework import Application

	a = Application()
	a._setUp()

	a = MovableText("Testing", "Test")
	print "0909090909090 - Finished!"

if __name__ == "__main__":
	test()

