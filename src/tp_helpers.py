"""Utility functions for working with thousand parsec objects/orders
"""

def getAbsPosition(obj):
	"""Returns the absolute position of an object"""
	return obj.Positional[0][0]

def getVelocity(obj):
	"""Returns the velocity of an object"""
	return obj.Positional[1][0]

def getOwner(obj):
	"""Returns the owner of an object"""
	return obj.Ownership[0][1]

def proxyToList(proxy):
	"""Transforms a TP Group Proxy into a list"""
	return [x for x in proxy]

