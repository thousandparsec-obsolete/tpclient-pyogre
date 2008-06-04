import math
from ctypes import *

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

def setWidgetText(name, text):
	"""Shortcut for setting CEGUI widget text.

	Examples of widget text are window titles, edit box text and button captions.
	"""
	wm = cegui.WindowManager.getSingleton()
	wm.getWindow(name).setText(text)

def bindEvent(name, object, method, event):
	"""Shortcut for binding a CEGUI widget event to a method"""
	wm = cegui.WindowManager.getSingleton()
	wm.getWindow(name).subscribeEvent(event, object, method)

def createSphere(name, radius, rings = 16, segments = 16):
	print "Creating Sphere"
	sphere = ogre.MeshManager.getSingleton().createManual(name, ogre.ResourceGroupManager.DEFAULT_RESOURCE_GROUP_NAME)
	sphere_vertex = sphere.createSubMesh()
	vertex_data = ogre.createVertexData()
	vertex_declaration = vertex_data.vertexDeclaration
	current_offset = 0

	# positions
	vertex_declaration.addElement(0, current_offset, ogre.VET_FLOAT3, ogre.VES_POSITION)
	current_offset += ogre.VertexElement.getTypeSize(ogre.VET_FLOAT3)

	# normals
	vertex_declaration.addElement(0, current_offset, ogre.VET_FLOAT3, ogre.VES_NORMAL)
	current_offset += ogre.VertexElement.getTypeSize(ogre.VET_FLOAT3)

	# texture coordinates
	vertex_declaration.addElement(0, current_offset, ogre.VET_FLOAT2, ogre.VES_TEXTURE_COORDINATES, 0)
	current_offset += ogre.VertexElement.getTypeSize(ogre.VET_FLOAT2)

	hw_manager = ogre.HardwareBufferManager.getSingleton()

	# allocate the vertex buffer
	vertex_data.vertexCount = (rings + 1) * (segments + 1)
	vertex_buffer = hw_manager.createVertexBuffer(
			vertex_declaration.getVertexSize(0),
			vertex_data.vertexCount,
			ogre.HardwareBuffer.HBU_STATIC_WRITE_ONLY,
			False)
	binding = vertex_data.vertexBufferBinding
	binding.setBinding(0, vertex_buffer)
	vertex = vertex_buffer.lock(ogre.HardwareBuffer.HBL_DISCARD)

	# allocate index buffer
	sphere_vertex.indexData.indexCount = 6 * rings * (segments + 1)
	sphere_vertex.indexData.indexBuffer = hw_manager.createIndexBuffer(
			ogre.HardwareIndexBuffer.IT_16BIT,
			sphere_vertex.indexData.indexCount,
			ogre.HardwareBuffer.HBU_STATIC_WRITE_ONLY,
			False)
	index_buffer = sphere_vertex.indexData.indexBuffer
	indices = index_buffer.lock(ogre.HardwareBuffer.HBL_DISCARD)

	delta_ring_angle = (math.pi / rings)
	delta_segment_angle = (2 * math.pi / segments)
	vertice_index = 0

	# generate the group of rings for the sphere
	for ring in range(rings):
		r0 = radius * math.sin(ring * delta_ring_angle)
		y0 = radius * math.cos(ring * delta_ring_angle)

		# generate the group of segments for the current ring
		for segment in range(segments):
			x0 = r0 * math.sin(segment * delta_segment_angle)
			z0 = r0 * math.cos(segment * delta_segment_angle)

			# add one vertex to the strip which makes up the sphere

