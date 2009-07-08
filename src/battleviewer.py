#! /usr/bin/env python

import os
import sys
import math

import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as cegui
import ogre.io.OIS as ois

import framework
import scene
import helpers
import starmap
import laser
import battlexml.battle as battle

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

class Participant(ogre.UserDefinedObject):
	""" Basic information is stored here for moving """

	def __init__(self, entity, speed=50.0):
		ogre.UserDefinedObject.__init__(self)
		self.speed = float(speed)
		self.movelist = []
		self.entity = entity
		self.distance = 0.0
		self.direction = ogre.Vector3().ZERO

	def addDest(self, dest):
		""" Takes in a tuple for dest """
		destination = ogre.Vector3(dest[0], dest[1], dest[2])
		self.movelist.insert(0, destination)

	def nextDest(self):
		try:
			self.destination = self.movelist.pop()
			sceneNode = self.entity.getParentSceneNode()
			self.direction = self.destination - sceneNode._getDerivedPosition()
			sceneNode.lookAt(self.destination, ogre.SceneNode.TransformSpace.TS_WORLD, ogre.Vector3().UNIT_Z)
			self.distance = self.direction.normalise()
			return True
		except IndexError:
			return False

class MoveFrameListener(ogre.FrameListener):
	""" Takes care of moving the ships """

	def __init__(self):
		ogre.FrameListener.__init__(self)
		self.entities = []

	def registerEntity(self, entity, sceneNode):
		if not (entity, sceneNode) in self.entities:
			self.entities.append((entity, sceneNode))

	def frameStarted(self, evt):
		for (entity, sceneNode) in self.entities:
			userObject = entity.getUserObject()
			if userObject.direction == ogre.Vector3().ZERO:
				userObject.nextDest()
			else:
				move = userObject.speed * evt.timeSinceLastFrame
				userObject.distance -= move
				if userObject.distance < 0.0:
					parentNode = sceneNode.getParentSceneNode()
					sceneNode.setPosition(parentNode._getDerivedOrientation().Inverse() * (userObject.destination - parentNode._getDerivedPosition()))
					userObject.direction = ogre.Vector3().ZERO
				else:
					sceneNode.translate(userObject.direction * move)
		return ogre.FrameListener.frameStarted(self, evt)

class GUIFadeListener(ogre.FrameListener):
	""" Fades GUI in/out """

	def __init__(self):
		ogre.FrameListener.__init__(self)
		self.elements = {}
		self.child_map = {}
		self.wm = cegui.WindowManager.getSingleton()

	def registerElement(self, element, min_alpha=0.01, fadeout_time=1.0, fadein_time=1.0):
		window = self.wm.getWindow(element)
		cur_alpha = window.getAlpha()
		self.elements[element] = {'min_alpha':min_alpha,
							'max_alpha':cur_alpha,
							'cur_alpha':cur_alpha,
							'alpha_step_in':(cur_alpha-min_alpha)/fadein_time,
							'alpha_step_out':(cur_alpha-min_alpha)/fadeout_time,
							'active':True,
							'direction':'out',
							'event':True}
		helpers.bindEvent(element, self, "show", cegui.Window.EventMouseEnters)
		helpers.bindEvent(element, self, "hide", cegui.Window.EventMouseLeaves)
		self.bindChildren(element, element)

	def bindChildren(self, name, base):
		window = self.wm.getWindow(name)
		num_children = window.getChildCount()
		for i in range(num_children):
			child = window.getChildAtIdx(i)
			child_name = child.getName().c_str()
			self.child_map[child_name] = base
			helpers.bindEvent(child_name, self, "show", cegui.Window.EventMouseEnters)
			helpers.bindEvent(child_name, self, "hide", cegui.Window.EventMouseLeaves)
			self.bindChildren(child_name, base)


	def show(self, evt, event_call=True):
		if isinstance(evt, str):
			element = evt
		else:
			element = evt.window.getName().c_str()
		if element in self.child_map:
			element = self.child_map[element]
		self.elements[element]['active'] = True
		self.elements[element]['event'] = event_call
		self.elements[element]['direction'] = 'in'

	def hide(self, evt, event_call=True):
		if isinstance(evt, str):
			element = evt
		else:
			element = evt.window.getName().c_str()
		if element in self.child_map:
			element = self.child_map[element]
		self.elements[element]['active'] = True
		self.elements[element]['event'] = event_call
		self.elements[element]['direction'] = 'out'

	def frameStarted(self, evt):
		for element in self.elements:
			properties = self.elements[element]
			if properties['active']:
				if properties['direction'] == 'in':
					delta_alpha = properties['alpha_step_in'] * evt.timeSinceLastFrame
					alpha = properties['cur_alpha']+delta_alpha
					if alpha >= properties['max_alpha']:
						alpha = properties['max_alpha']
						properties['active'] = False
						if not properties['event']:
							self.hide(element)
					self.wm.getWindow(element).setAlpha(alpha)
					properties['cur_alpha'] = alpha
				elif properties['direction'] == 'out':
					delta_alpha = properties['alpha_step_out'] * evt.timeSinceLastFrame
					alpha = properties['cur_alpha']-delta_alpha
					if alpha < properties['min_alpha']:
						alpha = properties['min_alpha']
						properties['active'] = False
						if not properties['event']:
							self.show(element)
					self.wm.getWindow(element).setAlpha(alpha)
					properties['cur_alpha'] = alpha

		return ogre.FrameListener.frameStarted(self, evt)

class BattleScene(scene.Scene):
	media = {
			'battleship':('plowshare', 75),
			'planet':('sphere_lod', 1500),
			'frigate':('frigate', 75),
			'scout':('scout', 50),
		}

	def __init__(self, parent, sceneManager):
		scene.Scene.__init__(self, parent, sceneManager)
		self.background_nodes = []
		self.sides = []
		self.bg_particle = None
		self.nodes = {}
		self.userobjects = {}
		self.listeners = {}

		self.camera_focus_node = self.rootNode.createChildSceneNode("CameraFocus")
		self.camera_node = self.camera_focus_node.createChildSceneNode("CameraNode")
		self.camera_node.attachObject(self.camera)
		self.camera_target_node = self.camera_focus_node.createChildSceneNode("CameraTarget")
		self.camera_target_node.position = self.camera_node.position
		self.h_angle = 0
		self.v_angle = 0

		root = ogre.Root.getSingleton()
		self.mfl = MoveFrameListener()
		root.addFrameListener(self.mfl)

		#self.createBackground()
		self.hide()

	def initial(self, sides):
		for side in sides:
			self.createSide(side)
		self.setStartingPositions(500)
		self.autofit()
		return self

	def setStartingPositions(self, radius):
		i = 1
		spacing = 360 / len(self.sides)
		for side in self.sides:
			interval = spacing * i
			interval = math.radians(interval)
			x = radius * math.cos(interval)
			y = radius * math.sin(interval)
			side.position = [x, y, 0]
			#side.lookAt(ogre.Vector3(0, 0, 0), ogre.SceneNode.TransformSpace.TS_WORLD)
			i += 1

	def createSide(self, side):
		print "creating side", side.id
		side_node = self.rootNode.createChildSceneNode("%s_node" % side.id)
		i = 0
		for entity in side.entities:
			i += 1
			print "creating", entity.name, entity.type
			node = side_node.createChildSceneNode("%s_node" % entity.id)
			media = self.media[entity.type]
			mesh = "%s.mesh" % media[0]
			entity_object = self.sceneManager.createEntity("%s" % entity.id, mesh)
			#entity_object.setNormaliseNormals(True)
			if entity.type == 'planet':
				entity_object.setMaterialName("Starmap/Planet/Terran")
				node.position = [-media[1] / 2 - media[1], 0, 0]
				#node.yaw(ogre.Radian(1.57))
			else:
				node.position = [0, i * 100, 0]
				node.yaw(ogre.Radian(1.57))
				node.roll(ogre.Radian(1.57))

				# orient ships to face each other
				node.yaw(ogre.Radian(3.13 * len(self.sides)))
				#node.pitch(ogre.Radian(3.14))
			obj_scale = media[1] / entity_object.mesh.boundingSphereRadius
			userObject = Participant(entity_object)
			entity_object.setUserObject(userObject)
			self.mfl.registerEntity(entity_object, node)
			node.attachObject(entity_object)
			node.setScale(ogre.Vector3(obj_scale, obj_scale, obj_scale))
			self.userobjects[entity.id] = userObject
			self.nodes[entity.id] = node

		self.sides.append(side_node)

	def createBackground(self):
		"""Creates a starry background for the current scene"""
		if self.bg_particle is None:
			self.bg_particle = self.sceneManager.createParticleSystem("star_layer1", "Space/Stars/Large")
		self.bg_particle.keepParticlesInLocalSpace = True
		particleNode = self.sceneManager.getSceneNode("CameraNode").createChildSceneNode("StarryBackgroundLayer1")
		particleNode.attachObject(self.bg_particle)
		#self.sceneManager.getSceneNode("CameraFocus").attachObject(self.bg_particle)
		#self.background_nodes.append(particleNode)

	def mouseMoved(self, evt):
		"""Handles the MouseMoved event

		If the middle mouse button is down pan the screen.
		Scrolling the mousewheel will zoom in and out.

		"""
		state = evt.get_state()

		if state.buttonDown(ois.MB_Middle):
			self.pan(state.X.rel * 50, -state.Y.rel * 50)

		elif state.buttonDown(ois.MB_Right):
			self.rotate(state.X.rel, state.Y.rel)

		elif state.Z.rel < 0:
			self.zoom(1000)

		elif state.Z.rel > 0:
			self.zoom(-1000)

		return False

	def zoom(self, amount):
		"""Zoom in or out for a set amount. Negative amounts will zoom in."""
		target = self.sceneManager.getSceneNode("CameraNode")
		z = target.position.z
		target.translate(0, 0, amount)

	def pan(self, x, y):
		cam_focus = self.sceneManager.getSceneNode("CameraFocus")
		cam_focus.translate(x, y, 0, ogre.SceneNode.TransformSpace.TS_LOCAL)

	def rotate(self, h_angle, v_angle):
		cam_focus = self.sceneManager.getSceneNode("CameraFocus")
		self.v_angle += v_angle
		self.h_angle += h_angle
		q = ogre.Quaternion(ogre.Degree(self.h_angle), ogre.Vector3().UNIT_Z)
		r = ogre.Quaternion(ogre.Degree(self.v_angle), ogre.Vector3().UNIT_X)
		q = q * r
		cam_focus.setOrientation(q)

	def autofit(self):
		"""Zooms out until all stars are visible"""
		fit = False
		camera = self.sceneManager.getCamera("PlayerCam")
		camera_node = self.sceneManager.getSceneNode("CameraNode")
		camera_node.position = ogre.Vector3(0, 0, 0)
		while not fit:
			camera_node.translate(0, 0, 1000)

			fit = True
			for obj in self.nodes.values():
				if not camera.isVisible(obj.position):
					fit = False


class BattleManager(framework.Application):
	"""Manage the battle through a collection of rounds, which trigger events via methods on the entities, also takes
	   care of managing other aspects of the battleviewer"""

	logTextArea = None
	laser = False

	def __init__(self, battle_file):
		framework.Application.__init__(self)

		self.battle = battle.parse_file(battle_file)
		self.rounds = []

		self.guiRenderer = 0
		self.guiSystem = 0
		self.application = DummyApplication()
		self.application.cache = DummyCache()

		self.running = True
		self.round = 0

	def _createScene(self):
		"""Setup CEGUI and create the various scenes"""
		# Initialise CEGUI Renderer
		self.guiRenderer = cegui.OgreCEGUIRenderer(self.renderWindow,
				   ogre.RENDER_QUEUE_OVERLAY, True, 0, self.sceneManager)
		self.guiSystem = cegui.System(self.guiRenderer)
		cegui.Logger.getSingleton().loggingLevel = cegui.Insane

		# Load Cegui Scheme
		cegui.SchemeManager.getSingleton().loadScheme("SleekSpace.scheme")
		self.guiSystem.setDefaultMouseCursor("SleekSpace", "MouseArrow")

		wmgr = cegui.WindowManager.getSingleton()
		root = helpers.loadWindowLayout("battleviewer.layout")
		self.guiSystem.setGUISheet(root)

		# Bind events to their respective buttons and set up other misc GUI stuff
		self.gfl = GUIFadeListener()
		ogre_root = ogre.Root.getSingleton()
		ogre_root.addFrameListener(self.gfl)
		helpers.bindEvent("Controls/Next", self, "next_round", cegui.PushButton.EventClicked)
		helpers.bindEvent("Controls/Prev", self, "prev_round", cegui.PushButton.EventClicked)
		helpers.bindEvent("Controls/Beginning", self, "beginning_round", cegui.PushButton.EventClicked)
		helpers.bindEvent("Controls/End", self, "end_round", cegui.PushButton.EventClicked)
		helpers.bindEvent("Controls/Stop", self, "stop_prog", cegui.PushButton.EventClicked)
		helpers.bindEvent("Controls/Play", self, "start_prog", cegui.PushButton.EventClicked)
		self.gfl.registerElement("Controls")
		self.gfl.registerElement("Logs")

		self.battlescene = BattleScene(self, self.sceneManager).initial(self.battle.sides)
		self.rounds = self.battle.rounds

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
		del self.laser
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

	def log_event(self, text):
		"""Displays the contents of the Log event on the screen for $DELAY seconds"""
		wm = cegui.WindowManager.getSingleton()
		window = wm.getWindow("Logs")
		oldtext = window.getText().c_str()
		window.setText(oldtext + text)
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
		self.log_event("%s fired at %s" % (attacker, victim))
		if not self.laser:
			self.laser = laser.Laser(self.sceneManager, "Laser/Laser/Solid") # Laser/Laser/PNG exists too, but I haven't been able to get it to work
		self.laser.fire(self.battlescene.nodes[attacker], self.battlescene.nodes[victim])
		#TODO: Add timer check to remove laser after a set amount of time or next laser fire (from the same side?)
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
		entity = self.battlescene.nodes[victim].getAttachedObject(0)
		#TODO: Progress through damage animations

	def death_event(self, ref):
		""" Causes the victim to disappear """
		if isinstance(ref, str):
			victim = ref
		else:
			victim = ref.id
		self.log_event("Death of %s" % victim)
		self.battlescene.nodes[victim].setVisible(False)
		#TODO: Explosion or burst of some sort before disappearance
		#TODO: Debris field

	def move_event(self, ref, dest):
		if isinstance(ref, str):
			mover = ref
		else:
			mover = ref.id
		self.log_event("%s moving to %r" % (mover, dest))
		userObject = self.battlescene.nodes[mover].getAttachedObject(0).getUserObject()
		userObject.addDest(dest)

	def update(self, evt):
		if self.running:
			round = self.rounds[self.round]
			for log in round.logs:
				self.log_event(log.content)
			for fire in round.fire:
				self.fire_event(fire.source, fire.destination)
			for damage in round.damage:
				self.damage_event(damage.reference, damage.amount)
			for death in round.death:
				self.death_event(death.reference)
			self.running = False
			self.round += 1
		return True

	# GUI stuff follows
	def next_round(self, evt):
		self.log_event("Going forward one round")
		if len(self.rounds) > self.round:
			self.running = True
			return True
		else:
			return False

	def prev_round(self, evt):
		self.log_event("Going back one round")

	def beginning_round(self, evt):
		self.log_event("Jumping to the beginning round")

	def end_round(self, evt):
		self.log_event("Jumping to the end round")

	def stop_prog(self, evt):
		self.log_event("Stopping round progression")

	def start_prog(self, evt):
		self.log_event("Starting round progression")

	def Cleanup(self):
		self.frameListener.keepRendering = False
		self.frameListener.destroy()

if __name__ == '__main__':
	app = BattleManager("battlexml/example1.xml")
	app.go()
	app.Cleanup()
