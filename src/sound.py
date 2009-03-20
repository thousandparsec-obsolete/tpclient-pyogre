import settings

sfx_buffer = {}

# Containers for looping sound files
music_list = []
sound_list = []

"""Helper functions for one-shot sounds"""
def clickSound(evt=None):
	"""Plays a click sound, can be used to register for a gui event"""
	if settings.sound_support and settings.sound_effects:
		from requirements import graphicsdir
		import pyglet
		import os
		sfx_file = os.path.join(graphicsdir, "sound/click.ogg")
		if sfx_file in sfx_buffer:
			sfx_buffer[sfx_file].play()
		else:
			if os.path.exists(sfx_file):
				sfx = pyglet.media.load(sfx_file, streaming=False)
				sfx_buffer[sfx_file] = sfx
				sfx.play()

