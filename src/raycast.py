import ogre.renderer.OGRE as ogre

# Raycasting to the polygon level, from
# http://www.ogre3d.org/wiki/index.php/Raycasting_to_the_polygon_level

def raycastFromPoint(point, normal, ray_scene_query):
	# create ray to test
	ray = ogre.Ray(ogre.Vector3(point.x, point.y, point.z),
					ogre.Vector3(normal.x, normal.y, normal.z))

	# create a query object
	ray_scene_query.setRay(ray)
	# execute the query, returns a vector of hits
	if (ray_scene_query.execute().size() <= 0):
		# raycast didn't hit any bounding boxes
		return False

	# at this point we have raycast to a series of different objects bounding boxes
	# we need to test these different objects to see which is the first polygon hit
	# there are some minor optimizations (distance based) that mean we wont have to
	# check all of the objects most of the time, but the worst case scenario is that
	# we need to test every triangle of every object.
	closest_distance = -1.0
	closest_result = ogre.Vector3()
	query_result = ray_scene_query.getLastResults()
	for i in range(0, query_result.size()):
		# stop checking if we have found a raycast hit that is closer
		# than all remaining entities
		if closest_distances >= 0.0 and closest_distance < query_result[i].distance:
			break
		# only check this result if its a hit against an entity
		if query_result[i].movable != None and query_result[i].movable.getMovableType().compare("Entity") == 0:
			# get the entity to check
			entity = query_result[i].movable
			parent_node = entity.getParentNode()
			# mesh data to retrieve
			(vertex_count, vertices, index_count, indices) = getMeshInformation(entity.getMesh(), \
					parent_node.getWorldPosition(), parent_node.getWorldOrientation(), \
					parent_node._getDerivedScale())
			# test for hitting individual triangles on the mesh
			new_closest_found = False
			for j in range(0, index_count, 3):
				# check for a hit against this triangle
				hit = ogre.Math.intersects(ray, vertices[indices[j]], vertices[indices[j+1]], vertices[indices[j+2]], True, False)
				# if it was a hit check if its the closest
				if hit.first:
					if closest_distance < 0.0 or hit.second < closest_distance:
						# this is the closest so far, save it off
						closest_distance = hit.second
						new_closest_found = True

			# free the vertices and indices memory
			del vertices
			del indices

			# if we found a new closest raycast for this object, update the
			# closest_result before moving on to the next object
			if new_closest_found:
				closest_result = ray.getPoint(closest_distance)
	if closest_distance >= 0.0:
		return closest_result
	else:
		return False

# get the mesh information for the given mesh
def getMeshInformation(mesh, position, orient, scale):
	added_shared = False
	current_offset = 0
	shared_offset = 0
	next_offset = 0
	index_offset = 0

	vertex_count = index_count = 0

	vertices = []
	indices = []

	# run through the submeshes, adding the data into the arrays
	for i in range(0, mesh.getNumSubMeshes()):
		submesh = mesh.getSubMesh(i)
		if submesh.useSharedVertices:
			vertex_data = mesh.sharedVertexData
		else:
			vertex_data = submesh.vertexData

		if not submesh.useSharedVertices or (submesh.useSharedVertices and not added_shared):
			if submesh.useSharedVertices:
				added_shared = True
				shared_offset = current_offset

			posElem = vertex_data.vertexDeclaration.findElementBySemantic(ogre.VES_POSITION)

			vbuf = vertex+data.vertexBufferBinding.getBuffer(posElem.getSource())

			vertex = vbuf.lock(ogre.HardwareBuffer.HBL_READ_ONLY)
			real = 0.0
			for j in range(0, vertex_data.vertexCount):
				posElem.baseVertexPointerToElement(vertex, real)
				pt = ogre.Vector3(real[0], real[1], real[2])
				vertices[current_offset + j] = (orient * (pt * scale)) + position
				vertex += vbuf.getVertexSize()
			vbuf.unlock()
			next_offset += vertex_data.vertexCount

		index_data = submesh.indexData
		numTris = index_data.indexCount / 3
		ibuf = index_data.indexBuffer

		use32bitindexes = (ibuf.getType() == ogre.HardwareIndexBuffer.IT_32BIT)

		long = ibuf.lock(ogre.HardwareBuffer.HBL_READ_ONLY)
		short = long

		if submesh.useSharedVertices:
			offset = shared_offset
		else:
			offset = current_offset

		if use32bitindexes:
			for k in range(0, numTris*3):
				indices[index_offset] = long[k] + offset
				index_offset += 1
		else:
			for k in range(0, numTris*3):
				indices[index_offset] = short[k] + offset
				index_offset += 1

		ibuf.unlock()
		current_offset = next_offset

	return (vertex_count, vertices, index_count, indices)

