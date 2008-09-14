import ogreal

import settings

sfx_buffer = {}

# Containers for looping sound files
music_list = []
sound_list = []

"""Helper functions for one-shot sounds"""
def clickSound(evt=None):
	"""Plays a click sound, can be used to register for a gui event"""
	if settings.sound_effects:
		from requirements import graphicsdir
		import pygame
		import os
		sfx_file = os.path.join(graphicsdir, "sound/click.ogg")
		if sfx_file in sfx_buffer:
			sfx_buffer[sfx_file].play()
		else:
			if os.path.exists(sfx_file):
				sfx = pygame.mixer.Sound(sfx_file)
				sfx_buffer[sfx_file] = sfx
				sfx.play()
		#sm = ogreal.SoundManager.getSingleton()
		#if sm.hasSound("click"):
			#click_fx = sm.getSound("click")
		#else:
			#click_fx = sm.createSound("click", "click.ogg", False)
		#click_fx.setPosition(sm.getListener().getPosition())
		#click_fx.play()

