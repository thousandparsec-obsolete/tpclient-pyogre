import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui

import framework
import helpers
import laser
import random
import torpedo

import battlexml.battle as battle

from battlegui import GUIFadeListener
from battlescene import BattleScene

class DummyCache(object):
	def __init__(self):
		self.objects = helpers.pickle_load("object")
		self.messages = helpers.pickle_load("message")
		self.designs = helpers.pickle_load("design")
		self.players = helpers.pickle_load("player")
		self.resources = helpers.pickle_load("resource")
		self.orders = {}

class DummyApplication(object):
	pass

class BattleManager(framework.Application):
	"""Manage the battle through a collection of rounds, which trigger events via methods on the entities, also takes
	   care of managing other aspects of the battleviewer"""

	logTextArea = None
	laser = False
	torpedo = False

	def __init__(self, battle_file):
		framework.Application.__init__(self)

		self.battle = battle.parse_file(battle_file)
		self.rounds = []
		self.event_queue = []
		self.post_event = None

		self.guiRenderer = 0
		self.guiSystem = 0
		self.application = DummyApplication()
		self.application.cache = DummyCache()

		self.running = True
		self.single = False
		self.round = 0

	def _createScene(self):
		"""Setup CEGUI and create the various scenes"""
		# Initialise CEGUI Renderer
		self.guiRenderer = cegui.OgreCEGUIRenderer(self.renderWindow,
				   ogre.RENDER_QUEUE_OVERLAY, True, 0, self.sceneManager)
		self.guiSystem = cegui.System(self.guiRenderer)
		cegui.Logger.getSingleton().loggingLevel = cegui.Insane

		# Load Cegui Scheme
		cegui.ImagesetManager.getSingleton().createImageset("controls.imageset")
		cegui.SchemeManager.getSingleton().loadScheme("SleekSpace.scheme")
		self.guiSystem.setDefaultMouseCursor("SleekSpace", "MouseArrow")

		wmgr = cegui.WindowManager.getSingleton()
		root = helpers.loadWindowLayout("battleviewer.layout")
		self.guiSystem.setGUISheet(root)

		# Bind events to their respective buttons and set up other misc GUI stuff
		self.gfl = GUIFadeListener()
		ogre_root = ogre.Root.getSingleton()
		ogre_root.addFrameListener(self.gfl)
		helpers.bindEvent("Controls/Next", self, "next_round", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Controls/Prev", self, "prev_round", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Controls/Beginning", self, "beginning_round", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Controls/End", self, "end_round", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Controls/Stop", self, "stop_prog", cegui.Window.EventMouseButtonDown)
		helpers.bindEvent("Controls/Play", self, "start_prog", cegui.Window.EventMouseButtonDown)
		self.gfl.registerElement("Controls")
		self.gfl.registerElement("Logs", 0.01, 3)

		self.battlescene = BattleScene(self, self.sceneManager).initial(self.battle.sides)
		self.rounds = self.battle.rounds

		self.queue_round()

		self.roundtimer = ogre.Timer()

		self.changeScene(self.battlescene)

		self.guiSystem.injectMousePosition(0, 0)

	def _createCamera(self):
		self.camera = self.sceneManager.createCamera("PlayerCam")
		self.camera.nearClipDistance = 5
		self.camera.setFixedYawAxis(True, ogre.Vector3().UNIT_Y)

	def _createFrameListener(self):
		self.frameListener = framework.CEGUIFrameListener(self, self.renderWindow, self.camera)
		self.root.addFrameListener(self.frameListener)
		self.frameListener.showDebugOverlay(True)

	def __del__(self):
		"""Clear variables

		This is needed to ensure the correct order of deletion.

		"""
		del self.camera
		del self.sceneManager
		del self.frameListener
		del self.guiSystem
		del self.guiRenderer
		del self.root
		del self.renderWindow

	def frameStarted(self, evt):
		if not self.frameListener.keepRendering:
			print "destroying"
			self.frameListener.destroy()

	def changeScene(self, scene):
		"""Function to change to a different scene"""
		if hasattr(self, "currentScene"):
			self.currentScene.hide()
		self.currentScene = scene
		self.currentScene.show()

	def log_event(self, text, event=True):
		"""Displays the contents of the Log event in the log box"""
		prefix = ""
		if event:
			prefix = "Round %d: " % int(self.rounds[self.round].number)
		wm = cegui.WindowManager.getSingleton()
		window = wm.getWindow("Logs")
		oldtext = window.getText().c_str()
		window.setText(oldtext + prefix + text)
		scrollbar = window.getVertScrollbar()
		scrollbar.setScrollPosition(scrollbar.getDocumentSize())
		self.gfl.show("Logs", False)

	def fire_event(self, ref_att, ref_vic):
		""" Takes in the names of an attacker and a victim for the fire event """
		if isinstance(ref_att, str):
			attacker = ref_att
			victim = ref_vic
		else:
			attacker = ref_att.id
			victim = ref_vic.id
		att_node = self.battlescene.nodes[attacker]
		vic_node = self.battlescene.nodes[victim]
		weapontype = att_node.getAttachedObject(attacker).getUserObject().battle_entity.weapontype
		self.log_event("%s fired at %s" % (attacker, victim))
		if weapontype == "torpedo":
			if not self.torpedo:
				self.torpedo = torpedo.Torpedo(self.sceneManager)
			self.torpedo.fire(self.battlescene.nodes[attacker], self.battlescene.nodes[victim])
			self.post_event = self.torpedo.clear
		else:
			if not self.laser:
				self.laser = laser.LaserManager(self.sceneManager, "Laser/Laser/Solid") # Laser/Laser/PNG exists too, but I haven't been able to get it to work
			self.laser.fire(self.battlescene.nodes[attacker], self.battlescene.nodes[victim])
			self.post_event = self.laser.clear
		#TODO: Move ships out of the way if they would inadvertantly be hit
		#TODO: Shield and hit animations
		#TODO: Taper laser for planets

	def damage_event(self, ref, amount):
		if isinstance(ref, str):
			victim = ref
		else:
			victim = ref.id
		self.log_event("%s was damaged for %d" % (victim, amount))
		camera = self.sceneManager.getCamera("PlayerCam")
		entity = self.battlescene.nodes[victim].getAttachedObject(victim)
		#TODO: Progress through damage animations

	def death_event(self, ref):
		""" Causes the victim to disappear """
		if isinstance(ref, str):
			victim = ref
		else:
			victim = ref.id
		self.log_event("Death of %s" % victim)
		explosion = "Explosion%d" % random.choice((1,2))
		self.death_particles = self.sceneManager.createParticleSystem("death_particles",explosion)
		self.victim = self.battlescene.nodes[victim].getAttachedObject(0)
		self.victim.setVisible(False)
		self.battlescene.nodes[victim].attachObject(self.death_particles)
		#TODO: Explosion or burst of some sort before disappearance
		#TODO: Debris field
		self.post_event = self.post_death

	def post_death(self):
		self.victim.setVisible(True)
		self.victim.getParentSceneNode().setVisible(False)
		self.victim = None
		self.death_particles.detatchFromParent()
		self.sceneManager.destroyParticleSystem("death_particles")

	def move_event(self, ref, dest):
		if isinstance(ref, str):
			mover = ref
		else:
			mover = ref.id
		self.log_event("%s moving to %r" % (mover, dest))
		userObject = self.battlescene.nodes[mover].getAttachedObject(mover).getUserObject()
		userObject.addDest(dest)

	def event_lock(self):
		""" If any locks are active, this should return true """
		result = False
		result = result or self.battlescene.wfl.warp_lock
		result = result or self.battlescene.mfl.move_lock()
		if self.torpedo:
			result = result or self.torpedo.torpedo_lock()
		return result

	def update(self, evt):
		# If everyone is still warping in from deep space, don't go on
		if self.event_lock():
			return True

		time = self.roundtimer.getMilliseconds()
		if self.running and time > 1000 and len(self.rounds) > self.round and not self.single:
			# If an event is still in progress don't go on
			if len(self.event_queue) == 0:
				self.round += 1
				if len(self.rounds) > self.round:
					self.queue_round(self.round)
				return True
			if self.post_event:
				self.post_event()
			event = self.event_queue.pop()
			self.execute(event)
			self.roundtimer.reset()

		if self.single:
			# Run through them all quick
			if len(self.event_queue) == 0:
				self.queue_round(self.round)
			for event in self.event_queue:
				if self.post_event:
					self.post_event()
				self.execute(event)
			self.event_queue = []
			self.running = False
			self.single = False
			self.round += 1
		return True

	def execute(self, event):
		# self.post_event should point to None or a function to deal with the event after its time is up
		self.post_event = None
		if isinstance(event, battle.Log):
			self.log_event(event.content)
		elif isinstance(event, battle.Fire):
			self.fire_event(event.source, event.destination)
		elif isinstance(event, battle.Damage):
			self.damage_event(event.reference, event.amount)
		elif isinstance(event, battle.Death):
			self.death_event(event.reference)
		elif isinstance(event, battle.Move):
			self.move_event(event.reference, (event.x, event.y, event.z))
		else:
			print "Unknown event type %s" % type(event)

	def queue_round(self, num=0):
		round = self.rounds[num]
		for event in round.events:
			self.event_queue.insert(0, event)
		return True

	def resurrect(self, round):
		""" Resurrects the dead and generally returns the round state to that of $round """
		# For moving
		for (entity, pos) in self.battlescene.initial_positions:
			self.battlescene.nodes[entity].setPosition(ogre.Vector3(pos[0], pos[1], pos[2]))
		for (entity, pos) in self.battle.states[round+1]['pos']:
			self.battlescene.nodes[entity].setPosition(ogre.Vector3(pos.x, pos.y, pos.z))
		# For death
		for entity in self.battlescene.nodes:
			if entity not in self.battle.states[round+1]['dead']:
				self.battlescene.nodes[entity].setVisible(True)
			else:
				self.battlescene.nodes[entity].setVisible(False)

	# GUI stuff follows
	def next_round(self, evt):
		if not self.battlescene.wfl.warp_lock:
			if len(self.rounds) > self.round:
				self.log_event("Going forward one round to round %d" % (self.round+1), False)
				self.single = True
				self.event_queue = []
				if self.post_event:
					self.post_event()
			else:
				self.log_event("At the last round", False)

	def prev_round(self, evt):
		if not self.battlescene.wfl.warp_lock:
			if self.round != 0:
				self.log_event("Going back one round to round %d" % (self.round-1), False)
				self.resurrect(self.round-1)
				self.round -= 1
				self.event_queue = []
				if self.post_event:
					self.post_event()
			else:
				self.log_event("At the first round", False)

	def beginning_round(self, evt):
		if not self.battlescene.wfl.warp_lock:
			self.log_event("Jumping to the beginning round", False)
			self.resurrect(0)
			self.round = 0
			self.event_queue = []
			self.running = False
			if self.post_event:
				self.post_event()

	def end_round(self, evt):
		if not self.battlescene.wfl.warp_lock:
			self.log_event("Jumping to the end round (round %d)" % (len(self.rounds)), False)
			self.resurrect(len(self.rounds)-1)
			self.round = len(self.rounds)-1
			self.event_queue = []
			self.running = False
			if self.post_event:
				self.post_event()

	def stop_prog(self, evt):
		self.log_event("Stopping round progression", False)
		self.running = False

	def start_prog(self, evt):
		self.log_event("Starting round progression", False)
		self.running = True
		self.roundtimer.reset()

	def Cleanup(self):
		self.frameListener.keepRendering = False
		self.frameListener.destroy()

