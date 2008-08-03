import ogre.sound.OgreAL as ogreal

import settings

"""Helper functions for one-shot sounds"""
def clickSound(evt=None):
	"""Plays a click sound, can be used to register for a gui event"""
	if settings.sound_effects:
		sm = ogreal.SoundManager.getSingleton()
		if sm.hasSound("click"):
			click_fx = sm.getSound("click")
		else:
			click_fx = sm.createSound("click", "click.ogg", False)
		click_fx.play()

