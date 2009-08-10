import copy

from xml.sax import make_parser
from xml.sax.handler import ContentHandler

class Battle:
	def __init__(self, version, media):
		self.version = version
		self.media = media
		self.sides = []
		self.rounds = []
		self.states = [{'dead':[], 'pos':[]}]

# Progression

class Round:
	def __init__(self, number):
		self.number = int(number)
		self.events = []
		self.logs = []
		self.fire = []
		self.damage = []
		self.death = []
		self.move = []

# Structure

class Side:
	def __init__(self, id):
		self.id = id
		self.entities = []

class Entity:
	def __init__(self, id):
		self.id = id
		self.name = ""
		self.type = ""
# Events

class Fire:
	def __init__(self):
		self.source = None
		self.destination = None

class Damage:
	def __init__(self):
		self.reference = None
		self.amount = 0

class Death:
	def __init__(self):
		self.reference = None

class Log:
	def __init__(self, content):
		self.content = content

class Move:
	def __init__(self):
		self.x = 0
		self.y = 0
		self.z = 0
		self.reference = None


class BattleXMLHandler(ContentHandler):
	def __init__(self):
		self.tags = []
		self.battle = None
		self.side = None
		self.entity = None
		self.types = []

	def setDocumentLocator(self, locator):
		self.locator = locator

	def startDocument(self):
		print "start document parsing"

	def endDocument(self):
		print "finished parsing"

	def startElement(self, name, attrs):
		self.tags.append(name)

		if name == "battle":
			self.battle = Battle(attrs['version'], attrs['media'])

		if name == "side":
			self.side = Side(attrs['id'])

		if name == "entity":
			self.entity = Entity(attrs['id'])
			self.types = ['name', 'type']

		if name == "round":
			self.round = Round(attrs['number'])
			self.types = ['log']

		if name == "fire":
			self.fire = Fire()

		if name == "damage":
			self.status = Damage()

		if name == "death":
			self.status = Death()

		if name == "move":
			self.status = Move()

		if name == "reference":
			ref = attrs['ref']
			setattr(self.status, name, self.findEntity(ref))

		if name in ['source', 'destination']:
			ref = attrs['ref']
			setattr(self.fire, name, self.findEntity(ref))

	def endElement(self, name):
		self.tags.pop()

		if name == "side":
			self.battle.sides.append(self.side)
			self.side = None

		if name == "entity":
			self.side.entities.append(self.entity)
			self.entity = None
			self.types = []

		if name == "round":
			self.battle.rounds.append(self.round)
			self.round = None
			self.types = []

		if name == "fire":
			self.round.events.append(self.fire)
			self.round.fire.append(self.fire)
			self.fire = None

		if name == "damage":
			self.round.events.append(self.status)
			self.round.damage.append(self.status)
			self.status = None

		if name == "death":
			self.round.events.append(self.status)
			self.round.death.append(self.status)
			self.status = None

		if name == "move":
			self.round.events.append(self.status)
			self.round.move.append(self.status)
			self.status = None

	def characters(self, content):
		tag = self.tags[len(self.tags) - 1]
		if tag == "log":
			log = Log(content)
			self.round.events.append(log)
			self.round.logs.append(log)

		if tag == "name":
			self.entity.name = content

		if tag == "type":
			self.entity.type = content

		if tag == "amount" and content.isdigit():
			self.status.amount = int(content)

		if tag == "position":
			pos = content.split(",")
			self.status.x = pos[0]
			self.status.y = pos[1]
			self.status.z = pos[2]

	def findEntity(self, id):
		for sides in self.battle.sides:
			for entity in sides.entities:
				if entity.id == id:
					return entity

def parse_states(battle):
	""" Gathers the final states for each round off battle """
	for round in battle.rounds:
		battle.states.append(copy.deepcopy(battle.states[round.number-1]))
		# This is a pain, because the battleviewer sets initial positions, so when you're
		# playing with the resurrect function on there you need to remember that if the move
		# state doesn't exist to consult the viewers tables
		for move in round.move:
			battle.states[round.number]['pos'].append((move.reference.id, move))
		for death in round.death:
			battle.states[round.number]['dead'].append(death.reference.id)
	return battle

def parse_file(file_name):
	parser = make_parser()
	handler = BattleXMLHandler()
	parser.setContentHandler(handler)
	parser.parse(open(file_name))
	battle = parse_states(handler.battle)
	return battle


if __name__ == "__main__":
	filename = raw_input("Filename: ")
	battle = parse_file(filename)
	for round in battle.rounds:
		for event in round.events:
			print str(event)
		for content in (event.content for event in round.events if isinstance(event, Log)):
			print content

	print "States"
	print "------"
	for i in range(len(battle.states)):
		print "Round %d" % i
		for state in battle.states[i]:
			print state + " - " + str(battle.states[i][state])
