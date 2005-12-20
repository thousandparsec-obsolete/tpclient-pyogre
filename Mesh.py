import math
from pyogre import ogre

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

	createSphere("Testing", 10, 2, 2)
	print "0909090909090 - Finished!"

if __name__ == "__main__":
	test()

