"""This module is used for playback of a splash screen or movie"""

import os
from requirements import graphicsdir

try:
	os.environ['SDL_VIDEO_CENTERED'] = '1'
	os.environ['SDL_VIDEO_WINDOW_POS'] = "center"
	import pygame
	import time

	if not os.path.exists(os.path.join(graphicsdir, "movies/intro-high.mpg")):
		print "Could not find the intro movie", os.path.join(graphicsdir, "movies/intro-high.mpg")
		raise ImportError

	pygame.init()
	screen = pygame.display.set_mode((640,480), pygame.NOFRAME)
	pygame.mixer.quit()
	movie = pygame.movie.Movie(os.path.join(graphicsdir, "movies/intro-high.mpg"))
	movie.set_display(screen, (0,0), )
	movie.play()
	pygame.display.flip()
	while True:
		if not movie.get_busy():
			break

		event = pygame.event.poll()
		if event.type == pygame.NOEVENT:
			time.sleep(0.1)
		elif event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN, pygame.KEYUP):
			break

	while movie.get_busy():
		movie.stop()

except ImportError:
	print "pygame not found - skipping splash movie"
