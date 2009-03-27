"""This module is used for playback of a splash screen or movie"""

import os
from requirements import graphicsdir

try:
	import pyglet

	if not os.path.exists(os.path.join(graphicsdir, "movies/intro-high.mpg")):
		print "Could not find the intro movie", os.path.join(graphicsdir, "movies/intro-high.mpg")
		raise ImportError

	source = pyglet.media.load(os.path.join(graphicsdir, "movies/intro-high.mpg"))
	player = pyglet.media.Player()
	player.queue(source)
	player.eos_action = pyglet.media.Player.EOS_PAUSE
	player.play()

	display = pyglet.window.get_platform().get_default_display()
	screen = display.get_default_screen()
	window = pyglet.window.Window(visible=False,
			style=pyglet.window.Window.WINDOW_STYLE_BORDERLESS)

	window.set_location(screen.width / 2 - window.width / 2, 
			screen.height / 2 - window.height / 2)
	window.set_visible(True)

	@window.event
	def on_draw():
		tex = player.get_texture()
		if tex:
			tex.blit(0, 0)

	@window.event
	def on_key_press(symbol, modifiers):
		pyglet.app.exit()

	@player.event
	def on_eos():
		pyglet.app.exit()

	pyglet.app.run()

except ImportError:
	print "pyglet not found - skipping splash movie"
