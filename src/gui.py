import htmllib
import formatter
import random

import ogre.gui.CEGUI as cegui
import ogre.renderer.OGRE as ogre
from tp.netlib.objects import OrderDescs
from tp.netlib.objects import parameters

import helpers
import scene
import settings
import tp_helpers
from tp.client import objectutils

ARG_ABS_COORD = 0
ARG_TIME = 1
ARG_OBJECT = 2
ARG_PLAYER = 3
ARG_RANGE = 5
ARG_LIST = 6
ARG_STRING = 7

ARG_PARAM_MAP = {
	parameters.OrderParamAbsSpaceCoords: 0,
	parameters.OrderParamTime: 1,
	parameters.OrderParamObject: 2,
	parameters.OrderParamPlayer: 3,
	parameters.OrderParamString: 7,
	parameters.OrderParamList: 6,
	parameters.OrderParamRange: 5
	}

ARG_GUI_MAP = {
		ARG_ABS_COORD:'Position',
		ARG_TIME:'Turns',
		ARG_LIST:'List',
		ARG_STRING:'String',
		ARG_OBJECT:'Objects',
		}

class Window(object):
	base = ""
	toggle_button = ""

	def __init__(self, parent):
		self.parent = parent
		if self.base != "":
			helpers.bindEvent(self.base, self, "closeClicked", cegui.FrameWindow.EventCloseClicked)

		if self.toggle_button != "":
			helpers.bindButtonEvent(self.toggle_button, self, "windowToggle")

	def closeClicked(self, evt):
		"""Called when user clicks on the close button of a window"""
		evt.window.setVisible(not evt.window.isVisible())

	def windowToggle(self, evt):
		"""Toggles visibility of a window"""
		# assume buttons and windows have the same name, minus prefix
		name = evt.window.getName().c_str().split("/")[1]
		if name != None:
			helpers.toggleWindow(name)

	def hide(self):
		"""Hides the window"""
		helpers.toggleWindow(self.base, False)

class MessageWindow(Window):
	base = "Messages"
	toggle_button = "Windows/Messages"

	def __init__(self, parent):
		Window.__init__(self, parent)
		self.clear()

		helpers.bindEvent("Messages/Next", self, "nextMessage", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Prev", self, "prevMessage", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Goto", self, "gotoMessageSubject", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Delete", self, "deleteMessage", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/MessageList", self, "selectMessage", cegui.MultiColumnList.EventSelectionChanged)

		wm = cegui.WindowManager.getSingleton()
		message_list = wm.getWindow("Messages/MessageList")
		message_list.addColumn("Subject", 0, cegui.UDim(0.7, 0))
		message_list.addColumn("Turn", 1, cegui.UDim(0.1, 0))
		message_list.setSelectionMode(cegui.MultiColumnList.RowSingle)
		self.message_list = message_list

	def clear(self):
		wm = cegui.WindowManager.getSingleton()
		message_list = wm.getWindow("Messages/MessageList")
		message_list.resetList()
		self.message_list_items = []
		self.messages = []
		self.message_index = 0
		self.goto_index = 0

	def create(self, cache):
		for val in cache.messages[0]:
			self.messages.append(val)

		if len(self.messages) > 0:
			if len(self.messages) > self.message_index:
				self.setCurrentMessage(self.messages[self.message_index])
			else:
				self.setCurrentMessage(self.messages[0])
			self.createMessageList()
			self.updateMessageList()

		self.updateTitlebar()

	def createMessageList(self):
		self.message_list.resetList()
		self.message_list_items = []

		for message_object in self.messages:
			message = message_object.CurrentOrder
			index = self.message_list.addRow()
			item = cegui.ListboxTextItem(str(message.subject))
			item.setAutoDeleted(False)
			item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
			self.message_list.setItem(item, 0, index)
			self.message_list_items.append(item)

			item = cegui.ListboxTextItem(str(message.turn))
			item.setAutoDeleted(False)
			self.message_list.setItem(item, 1, index)
			self.message_list_items.append(item)

	def updateMessageList(self):
		reference = cegui.MCLGridRef(self.message_index, 0)
		self.message_list.setItemSelectState(reference, True)

	def updateTitlebar(self):
		helpers.setWidgetText("Messages", "Messages (%d/%d)" % (self.message_index + 1, len(self.messages)))

	def selectMessage(self, evt):
		selected = self.message_list.getFirstSelectedItem()
		index = self.message_list.getItemRowIndex(selected)
		self.setCurrentMessage(self.messages[index])
		self.message_index = index
		self.updateTitlebar()

	def nextMessage(self, evt):
		"""Sets messagebox to the next message if available"""
		if len(self.messages) > 0 and self.message_index < len(self.messages) - 1:
			self.message_index += 1
			self.goto_index = 0
			self.setCurrentMessage(self.messages[self.message_index])
		self.updateTitlebar()
		self.updateMessageList()

	def prevMessage(self, evt):
		"""Sets messagebox to the previous message if available"""
		if len(self.messages) > 0 and self.message_index > 0:
			self.message_index -= 1
			self.goto_index = 0
			self.setCurrentMessage(self.messages[self.message_index])
		self.updateTitlebar()
		self.updateMessageList()

	def deleteMessage(self, evt):
		"""Deletes the current message permanently and displays the next message, if any."""
		cache = self.parent.getCache()
		network = self.parent.parent.application.network
		current_message = self.messages[self.message_index]
		change_node = cache.messages[0][current_message.id]
		evt = cache.apply("messages", "remove", 0, change_node, None)
		network.Call(network.OnCacheDirty, evt)
		self.messages.remove(current_message)
		if len(self.messages) > 0:
			self.nextMessage(evt)
		else:
			helpers.setWidgetText("Messages/Message", "")
		self.createMessageList()
		self.updateTitlebar()

	def gotoMessageSubject(self, evt):
		"""Select and center on the subject of a message.

		Cycles through available subjects if there are more than one.

		"""
		message = self.messages[self.message_index].CurrentOrder
		refs = message.references
		if self.goto_index >= len(refs):
			self.goto_index = 0
		i = 0
		for reference in refs:
			print reference
		for reference in refs:
			i += 1
			if reference[0] is scene.OBJECT:
				id = reference[1]
				if id is scene.UNIVERSE: # universe
					continue
				if i < self.goto_index + 1:
					continue
				if self.parent.selectObjectById(id):
					self.parent.starmap.center(id)
					self.goto_index = i
					break

	def setCurrentMessage(self, message_object):
		"""Sets message text inside message window"""
		message = message_object.CurrentOrder
		text = "Subject: " + message.subject + "\n"
		text += "\n"
		text += self.format(message.body).output
		helpers.setWidgetText("Messages/Message", text)

	def format(self, text):
		writer = SimpleWriter()
		format = formatter.AbstractFormatter(writer)
		parser = htmllib.HTMLParser(format)
		parser.feed(text)
		parser.close()
		return writer

class SimpleWriter(formatter.NullWriter):
	output = ""

	def send_flowing_data(self, data):
		self.output += data

	def send_line_break(self):
		self.output += "\n"

class ArgumentsWindow(object):
	def __init__(self, parent):
		self.arguments = []
		self.arguments_pending_update = []
		self.parent = parent
		self.id = None
		self.order_subtype = None
		self.order_node = None

		self.selection_list = {}
		self.listbox_queue = {}
		self.update_list = {}
		self.attributes = {}
		self.object_list = {}

		helpers.bindEvent("Arguments", self, "hide", cegui.FrameWindow.EventCloseClicked)
		helpers.bindEvent("Arguments/Cancel", self, "hide", cegui.PushButton.EventClicked)
		helpers.bindEvent("Arguments/Save", self, "confirm", cegui.PushButton.EventClicked)
		for win in ['Turns', 'Position', 'List', 'Objects', 'String']:
			helpers.toggleWindow("Arguments/%s" % win, False)
		self.hide()

	def hide(self, evt=None):
		"""Hide the argument window"""
		helpers.toggleWindow("Arguments", False)
		print self.arguments
		for arg in self.arguments:
			cegui.WindowManager.getSingleton().destroyWindow(arg)
		self.arguments = []
		self.arguments_pending_update = []
		self.order_subtype = None
		self.id = None
		self.order_node = None

	def getArguments(self):
		"""Return a list containing arguments for this order"""
		wm = cegui.WindowManager.getSingleton()
		arguments = []
		for argument in self.arguments:
			name = argument.name.c_str()
			base = name[name.rfind('/') + 1:]
			print name, base
			if base == "Position":
				value = []
				for elem in ['X', 'Y', 'Z']:
					elem_widget = wm.getWindow("%s/%s" % (name, elem))
					text = elem_widget.text.c_str()
					value.append(long(text))
			elif base == "Turns":
				elem_widget = wm.getWindow("%s/Editbox" % name)
				# FIXME using hardcoded values
				value = (long(elem_widget.text.c_str()), 100)
			elif base == "List":
				elem_widget = wm.getWindow("%s/Listbox" % name)
				update_list = self.update_list[name]
				del self.update_list[name]
				value = [update_list, []]
				for key, queue in self.listbox_queue.items():
					for update_item in update_list:
						item_id = update_item[0]
						item_name = update_item[1]
						if item_name == key:
							value[1].append((item_id, int(queue[0].text.c_str())))
							break
			elif base == "String":
				elem_widget = wm.getWindow("%s/String" % name)
				text = elem_widget.text.c_str()
				# FIXME using hardcoded values
				value = [1024, unicode(text)]
			elif base == "Objects":
				elem_widget = wm.getWindow("%s/Object" % name)
				text = elem_widget.text.c_str()
				if not text.isdigit():
					text = text.rpartition('(')[2]
					text = text.replace(')', '')
					if not text.isdigit():
						print "Error with object argument", text
						self.hide()
						return None
				value = [long(text)]
			else:
				self.hide()
				return None
			arguments += [value]

		return arguments

	def confirm(self, evt):
		"""Fill an order with arguments and send to the server"""
		print "Sending Order"
		wm = cegui.WindowManager.getSingleton()

		order_description = OrderDescs()[self.order_subtype]
		print order_description
		orderargs = [0, self.id, -1, order_description.subtype, 0, []]

		orderargs += self.getArguments()

		order = order_description(*orderargs)
		if self.order_node:
			self.parent.sendOrder(self.id, order, "change", self.order_node)
			self.order_node = None
		else:
			self.parent.sendOrder(self.id, order)
		self.hide()

	def show(self, name):
		"""Display the argument window

		name parameter sets the window title.

		"""
		wm = cegui.WindowManager.getSingleton()
		args = wm.getWindow("Arguments")
		args.show()
		args.activate()
		args.text = name

	def setCurrentOrder(self, id, order_subtype):
		"""Set the order type and object id for sending the order"""
		self.id = id
		self.order_subtype = order_subtype

	def addArgument(self, caption, argument):
		"""Add an argument widget to the argument window

		argument parameter is one of the predefined TP arguments e.g. list, string, etc

		"""
		wm = cegui.WindowManager.getSingleton()
		index = len(self.arguments)
		parent = wm.getWindow("Arguments/Pane")

		try:
			base_name = ARG_GUI_MAP[argument]
		except KeyError:
			print "Unsupported argument"
			return None

		base = wm.getWindow("Arguments/%s" % base_name)
		widget = helpers.copyWindow(base, "Argument%i" % index)

		prefix = (index, base_name)
		caption_widget = wm.getWindow("Argument%i/%s/Caption" % prefix)
		caption_widget.text = caption.capitalize()
		parent.addChildWindow(widget)

		if argument is ARG_LIST:
			self.arguments_pending_update.append((ARG_LIST, widget, caption))
			list_widget = wm.getWindow("Argument%i/%s/Listbox" % prefix)
			list_widget.addColumn("#", 0, cegui.UDim(0.3, 0))
			list_widget.addColumn("Type", 1, cegui.UDim(0.5, 0))
			list_widget.setSelectionMode(cegui.MultiColumnList.RowSingle)
			helpers.bindEvent("Argument%i/%s/Add" % prefix, self, "addItemToList", cegui.PushButton.EventClicked)
		if argument is ARG_OBJECT:
			# populate the listbox with universe items
			list_widget = wm.getWindow("Argument%i/%s/Object" % prefix)
			for id, obj in self.parent.objects.items():
				item = cegui.ListboxTextItem("%s (%i)" % (obj.name, id))
				#print item.text
				item.setAutoDeleted(False)
				if prefix in self.object_list:
					self.object_list[prefix].append(item)
				else:
					self.object_list[prefix] = [item]
				list_widget.addItem(item)

		# push the new widget down so it doesn't overlap
		offset_x = cegui.UDim(0, 0)
		offset_y = cegui.UDim(0, 0)
		for arg_widget in self.arguments:
			offset_y += arg_widget.position.d_y + arg_widget.height
		widget.position += cegui.UVector2(offset_x, offset_y)
		self.arguments.append(widget)

		return widget

	def addItemToList(self, evt):
		"""Append or add a new item to an existing list argument widget"""
		#print "addItemToList", evt.window.name, evt.window.parent.name
		prefix = evt.window.parent.name.c_str()
		wm = cegui.WindowManager.getSingleton()
		listbox = wm.getWindow("%s/Listbox" % prefix)
		selection_widget = wm.getWindow("%s/Selection" % prefix)
		current_selection = selection_widget.text.c_str()

		if self.update_list.has_key(prefix) and self.selection_list.has_key(current_selection):
			selection_list = self.update_list[prefix]
			for triplet in selection_list:
				selection_id = triplet[0]
				selection_name = triplet[1]
				if selection_name == current_selection:
					print selection_id, selection_name, "selected"

					if self.listbox_queue.has_key(current_selection):
						queue = self.listbox_queue[current_selection]
						for item in queue:
							if item.text.c_str() == selection_name and listbox.isListboxItemInList(item):
								#print "Existing queue item found"
								grid = listbox.getItemGridReference(item)
								grid.column = 0
								value_item = listbox.getItemAtGridReference(grid)
								value = int(value_item.text.c_str())
								value_item.text = str(value + 1)
								#print "Value set:", value, grid
								listbox.handleUpdatedItemData()
								return
					else:
						queue = []
						self.listbox_queue[current_selection] = queue

					index = listbox.addRow()

					item = cegui.ListboxTextItem(str(1))
					item.setAutoDeleted(False)
					item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
					listbox.setItem(item, 0, index)
					queue.append(item)

					item = cegui.ListboxTextItem(selection_name)
					item.setAutoDeleted(False)
					item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
					listbox.setItem(item, 1, index)
					queue.append(item)

	def setValues(self, order_node):
		"""Update argument widgets with values from an order node"""
		wm = cegui.WindowManager.getSingleton()
		self.order_node = order_node
		order = order_node.CurrentOrder
		order_description = OrderDescs()[order._subtype]
		widgets = self.arguments[:]

		# assume that argument widgets are created in the same order as order_description
		for name, argument in order_description.names:
			widget = widgets[0]
			del widgets[0]
			prefix = widget.name.c_str()

			base_name = ARG_GUI_MAP[argument]
			print base_name, name
			value = getattr(order, name)
			print value

			if base_name == "Position":
				i = 0
				for elem in ['X', 'Y', 'Z']:
					wm.getWindow("%s/%s" % (prefix, elem)).setText(str(value[i]))
					i += 1
			elif base_name == "Turns":
				elem_widget = wm.getWindow("%s/Editbox" % prefix)
				elem_widget.setText(str(value))
			elif base_name == "List":
				elem_widget = wm.getWindow("%s/Listbox" % prefix)
				index = elem_widget.addRow()
				for tuple in value[1]:
					selection_name = None
					selection_id = tuple[0]
					for selection in value[0]:
						if selection[0] == selection_id:
							selection_name = selection[1]
					if not selection_name:
						break
					queue = []
					self.listbox_queue[selection_name] = queue

					item = cegui.ListboxTextItem(str(tuple[1]))
					item.setAutoDeleted(False)
					item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
					elem_widget.setItem(item, 0, index)
					queue.append(item)

					item = cegui.ListboxTextItem(selection_name)
					item.setAutoDeleted(False)
					item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
					elem_widget.setItem(item, 1, index)
					queue.append(item)
			elif base_name == "String":
				elem_widget = wm.getWindow("%s/String" % prefix)
				elem_widget.setText(str(value[1]))
			elif base_name == "Objects":
				elem_widget = wm.getWindow("%s/Object" % prefix)
			else:
				self.hide()
				return None

	def update(self):
		"""Updates any lists in the arguments window upon receiving from the server"""
		#print "Updating list items"
		if self.id != None and self.order_subtype != None:
			cache = self.parent.getCache()
			queue_id = objectutils.getOrderQueueList(cache, self.id)[0][1]
			order = cache.orders[queue_id].last.CurrentOrder
			for triplet in self.arguments_pending_update:
				#print triplet
				arg_type = triplet[0]
				argument = triplet[1]
				attribute = triplet[2]

				if arg_type is ARG_LIST:
					if order is None:
						print "order is none"
						break
					update_list = getattr(order, attribute)[0]
					selection = argument.getChild("%s/Selection" % argument.name.c_str())
					print selection, selection.name, update_list
					self.update_list[argument.name.c_str()] = update_list

					selection.resetList()
					self.selection_list = {}

					for element in update_list:
						#print element[1]
						item = cegui.ListboxTextItem(element[1])
						item.setAutoDeleted(False)
						selection.addItem(item)
						if self.selection_list.has_key(element[1]):
							self.selection_list[element[1]].append(item)
						else:
							self.selection_list[element[1]] = [item]

			self.arguments_pending_update = []

class DesignsWindow(Window):
	base = "Designs"
	toggle_button = "TopBar/Designs"

	def __init__(self, parent):
		Window.__init__(self, parent)
		self.clear()

		# store as [ListboxTextItem : design_id] pairs
		helpers.bindEvent("Designs/DesignList", self, "selectDesign", cegui.Listbox.EventSelectionChanged)

		current_design = cegui.WindowManager.getSingleton().getWindow("Designs/CurrentDesign")
		current_design.addColumn("#", 0, cegui.UDim(0.3, 0))
		current_design.addColumn("Component", 1, cegui.UDim(0.5, 0))
		current_design.setSelectionMode(cegui.MultiColumnList.RowSingle)

	def clear(self):
		wm = cegui.WindowManager.getSingleton()
		design_list = wm.getWindow("Designs/DesignList")
		design_list.resetList()
		current_design = wm.getWindow("Designs/CurrentDesign")
		current_design.resetList()
		self.design_list_items = {}
		self.current_design_items = []

	def populateDesignsWindow(self, designs):
		"""Fill the design window with designs"""
		wm = cegui.WindowManager.getSingleton()
		designlistbox = wm.getWindow("Designs/DesignList")
		r = random.random

		for design in designs.values():
			item = cegui.ListboxTextItem(design.name)
			item.setSelectionBrushImage("SleekSpace", "ClientBrush")
			item.setSelectionColours(cegui.colour(0.9, 0.9, 0.9))
			item.setAutoDeleted(False)
			random.seed(design.owner)
			item.setTextColours(cegui.colour(r(), r(), r()))
			self.design_list_items[item] = design.id
			designlistbox.addItem(item)

	def selectDesign(self, evt):
		"""Select a design from the design list"""
		wm = cegui.WindowManager.getSingleton()
		designlistbox = wm.getWindow("Designs/DesignList")
		selected = designlistbox.getFirstSelectedItem()
		cache = self.parent.getCache()

		if selected:
			current_design = wm.getWindow("Designs/CurrentDesign")
			current_design.resetList()
			self.current_design_items = []

			design_id = self.design_list_items[selected]
			design = cache.designs[design_id]
			owner = cache.players[design.owner].name
			helpers.setWidgetText("Designs", "Ship Designs - %s's %s" % (owner, design.name))

			components = cache.components
			for component in design.components:
				id = component[0]
				total = component[1]
				component_info = components[id]
				index = current_design.addRow()

				# The number of components
				item = cegui.ListboxTextItem(str(total))
				item.setAutoDeleted(False)
				item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
				current_design.setItem(item, 0, index)
				self.current_design_items.append(item)

				# The name of the component
				item = cegui.ListboxTextItem(component_info.name)
				item.setAutoDeleted(False)
				item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
				current_design.setItem(item, 1, index)
				self.current_design_items.append(item)

			information_string = ""
			properties = cache.properties
			for property in design.properties:
				id = property[0]
				value = property[1]
				new_line = properties[id].display_name
				# TODO: Align values to the right-hand side
				#new_line = new_line.ljust(100 - len(new_line))
				new_line += " - "
				new_line += "%s\n" % value
				information_string += new_line
			helpers.setWidgetText("Designs/Information", information_string)

class InformationWindow(Window):
	base = "Information"
	toggle_button = "Windows/Information"

	def clear(self):
		helpers.setWidgetText("Information/Text", "")

	def setText(self, object):
		"""Sets text inside information window"""
		cache = self.parent.getCache()
		text = ""
		text += "Name: %s (%s)\n" % (str(object.name), str(object.id))
		text += "Position: %s\n" % str(tp_helpers.getAbsPosition(object))
		text += "Velocity: %s\n" % str(tp_helpers.getVelocity(object))
		text += "Size: %s\n" % str(object.size)
		if hasattr(object, "Ownership"):
			owner = tp_helpers.getOwner(object)
			if owner != -1:
				owner_name = cache.players[owner].name
				race_name = cache.players[owner].race_name
				text += "Owner: %s(%s)\n" % (owner_name, race_name)
			else:
				text += "Neutral\n"
		if hasattr(object, "Ships"):
			text += "-- Ships --\n"
			ships = []
			total = 0
			for group in object.Ships[0]:
				group = group[0]
				design_name = cache.designs[group[1]].name
				text += "    %s: %i\n" % (design_name, group[2])
		if hasattr(object, "Resources"):
			text += "-- Resources --\n"
			resources = []
			print object.Resources
			for resource in object.Resources:
				if len(resource[0]) > 0:
					resource = resource[0][0]
					info = cache.resources[resource[0]]
					resource_string = "    %s: %s available, %s minable, %s inaccessable" % \
						(info.name_plural, resource[1], resource[2], resource[3])
					text += resource_string
		helpers.setWidgetText("Information/Text", text)

class SystemWindow(Window):
	base = "System"
	toggle_button = "Windows/System"

	def __init__(self, parent):
		Window.__init__(self, parent)
		self.clear()
		helpers.bindEvent("System/SystemList", self, "systemSelected", cegui.Listbox.EventSelectionChanged)
		helpers.bindEvent("System/SystemList", self, "systemSelected", cegui.Window.EventMouseDoubleClick)
		helpers.bindEvent("System/SystemFilter", self, "filterSystems", cegui.Editbox.EventTextChanged)

	def clear(self):
		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("System/SystemList").resetList()
		self.system_list = []
		wm.getWindow("System/SystemFilter").setText("")

	def create(self, cache):
		wm = cegui.WindowManager.getSingleton()
		listbox = wm.getWindow("System/SystemList")
		for object in cache.objects.values():
			if object._subtype is scene.STAR:
				item = cegui.ListboxTextItem(object.name)
				item.setSelectionBrushImage("SleekSpace", "ClientBrush")
				item.setSelectionColours(cegui.colour(0.9, 0.9, 0.9))
				item.setAutoDeleted(False)
				self.system_list.append(item)
				listbox.addItem(item)

	def systemSelected(self, evt):
		"""Updates information box with selected system info"""
		wm = cegui.WindowManager.getSingleton()
		listbox = wm.getWindow("System/SystemList")
		selected = listbox.getFirstSelectedItem()
		if selected:
			for obj in self.parent.objects.values():
				if obj.name == selected.text:
					if hasattr(evt, "clickCount"):
						self.parent.selectObjectById(obj.id, True)
					else:
						self.parent.selectObjectById(obj.id, False)
					break

	def filterSystems(self, evt):
		"""Filters the systems based on prefix"""
		system_prefix = evt.window.getText().c_str()
		wm = cegui.WindowManager.getSingleton()
		listbox = wm.getWindow("System/SystemList")
		listbox.resetList()
		cache = self.parent.getCache()
		for object in cache.objects.values():
			if object._subtype is scene.STAR:
				if (object.name.lower().startswith(system_prefix.lower())):
					item = cegui.ListboxTextItem(object.name)
					item.setSelectionBrushImage("SleekSpace", "ClientBrush")
					item.setSelectionColours(cegui.colour(0.9, 0.9, 0.9))
					item.setAutoDeleted(False)
					self.system_list.append(item)
					listbox.addItem(item)

class OrdersWindow(Window):
	base = "Orders"
	toggle_button = "Windows/Orders"

	defaults = {
		parameters.OrderParamAbsSpaceCoords: [[0,0,0]],
		parameters.OrderParamTime: [[0, 0]],
		parameters.OrderParamObject: [[0, []]],
		parameters.OrderParamPlayer: [[0, 0]],
		parameters.OrderParamString: [[0, ""]],
		parameters.OrderParamList: [[[], []]],
		parameters.OrderParamRange: [[-1, -1, -1, -1]],
	}

	def __init__(self, parent):
		Window.__init__(self, parent)
		self.clear()

		helpers.bindEvent("Orders/Delete", self, "deleteOrder", cegui.PushButton.EventClicked)
		helpers.bindEvent("Orders/NewOrder", self, "newOrder", cegui.PushButton.EventClicked)
		helpers.bindEvent("Orders/Edit", self, "editOrder", cegui.PushButton.EventClicked)

		wm = cegui.WindowManager.getSingleton()
		order_queue = wm.getWindow("Orders/OrderQueue")
		order_queue.addColumn("Type", 0, cegui.UDim(0.4, 0))
		order_queue.addColumn("Turns left", 1, cegui.UDim(0.4, 0))
		order_queue.setSelectionMode(cegui.MultiColumnList.RowSingle)

		self.arguments_window = ArgumentsWindow(parent)
		self.update_order = None
		self.update_id = None

	def clear(self):
		wm = cegui.WindowManager.getSingleton()
		order_queue = wm.getWindow("Orders/OrderQueue")
		order_queue.resetList()
		order_list = wm.getWindow("Orders/OrderList")
		order_list.resetList()

		self.order_queue_items = []
		self.order_queue_list = []

	def update(self):
		self.arguments_window.update()
		if self.update_id != None and self.update_order != None:
			# remove the empty order
			self.parent.sendOrder(self.update_id, self.update_order, "remove")
			self.update_id = self.update_order = None

	def hideArguments(self):
		self.arguments_window.hide()

	def updateOrdersWindow(self, id, cache):
		"""Update the order queue and available orders in the orders window

		Returns True if the window is updated successfully.

		"""
		wm = cegui.WindowManager.getSingleton()
		order_queue = wm.getWindow("Orders/OrderQueue")
		order_list = wm.getWindow("Orders/OrderList")
		order_queue.resetList()
		order_list.resetList()
		order_list.setText("")

		self.order_queue_items = []
		self.order_queue_list = []

		order_types = objectutils.getOrderTypes(cache, id)
		if len(order_types) <= 0:
			return False

		object = cache.objects[id]

		queuelist = cache.orders[objectutils.getOrderQueueList(cache, id)[0][1]]
		for o_node in queuelist:
			index = order_queue.addRow()
			order = o_node.CurrentOrder
			self.order_queue_list.append(o_node)
			item = cegui.ListboxTextItem(order._name)
			item.setAutoDeleted(False)
			item.setSelectionBrushImage("SleekSpace", "MultiListSelectionBrush")
			self.order_queue_items.append(item)
			order_queue.setItem(item, 0, index) # col id, row id

			item = cegui.ListboxTextItem(str(order.turns))
			item.setAutoDeleted(False)
			order_queue.setItem(item, 1, index)
			self.order_queue_items.append(item)

		if len(order_types) > 0:
			self.orders = {}
			descs = OrderDescs()
			for order_type in order_types.popitem()[1]:
				if not descs.has_key(order_type):
					continue
				description = descs[order_type]
				item = cegui.ListboxTextItem(description._name)
				item.setAutoDeleted(False)
				self.orders[order_type] = item
				order_list.addItem(item)

		return True

	def newOrder(self, evt=None):
		"""Callback when user clicks the New button in orders window"""
		wm = cegui.WindowManager.getSingleton()
		order_list = wm.getWindow("Orders/OrderList")
		item = order_list.getSelectedItem()
		if item:
			index = order_list.getItemIndex(item)
			self.showOrder(index=index)

	def showOrder(self, evt=None, index=None):
		"""Show the arguments for a selected order

		evt is used if the method is a callback from CEGUI
		index is used to indicate which of the available orders to show
		Either evt or index will be used only, the other parameter can be None

		"""
		if evt:
			index = int(evt.window.name.c_str()[17:])
		if index == None:
			print "no valid index"
			return None
		id = self.parent.getIDFromMovable(self.parent.current_object)
		cache = self.parent.getCache()
		object = cache.objects[id]
		descs = OrderDescs()
		orders = []
		for order_type in objectutils.getOrderTypes(cache, id).popitem()[1]:
			if not descs.has_key(order_type):
				continue
			orders.append(descs[order_type])
		order_description = orders[index]

		self.arguments = []
		orderargs = [0, id, -1, order_description.subtype, 0, []]
		for prop in order_description.properties:
			orderargs += self.defaults[type(prop)]

		order = order_description(*orderargs)

		# need to send an empty order to get allowable choices e.g. production
		self.parent.sendOrder(id, order)

		for prop in order_description.properties:
			print "adding argument", prop
			self.arguments_window.addArgument(prop.name, ARG_PARAM_MAP[type(prop)])

		self.arguments_window.show(order_description._name)
		self.arguments_window.setCurrentOrder(id, order_description.subtype)
		self.update_order = order
		self.update_id = id

	def getCurrentOrder(self):
		"""Return the order node selected in the order queue list"""
		id = self.parent.getIDFromMovable(self.parent.current_object)
		cache = self.parent.getCache()
		object = cache.objects[id]
		wm = cegui.WindowManager.getSingleton()
		order_queue = wm.getWindow("Orders/OrderQueue")
		selected = order_queue.getFirstSelectedItem()
		if selected:
			index = order_queue.getItemRowIndex(selected)
			o_node = self.order_queue_list[index]
			return o_node
		else:
			return None

	def deleteOrder(self, evt):
		"""Callback which deletes an order in the selected order queue"""
		o_node = self.getCurrentOrder()
		if o_node:
			self.parent.sendOrder(o_node.CurrentOrder.id, o_node.CurrentOrder, "remove", o_node)

	def editOrder(self, evt):
		"""Callback which allows the user to edit an order"""
		o_node = self.getCurrentOrder()
		if o_node:
			order = o_node.CurrentOrder
			item = self.orders[order._subtype]
			wm = cegui.WindowManager.getSingleton()
			index = wm.getWindow("Orders/OrderList").getItemIndex(item)
			self.showOrder(index=index)
			self.arguments_window.setValues(o_node)

class ConfigWindow(object):
	max_zoom_speed = 10
	min_zoom_speed = 1

	def __init__(self, window):
		self.config = helpers.loadWindowLayout("config.layout")
		window.addChildWindow(self.config)
		helpers.bindButtonEvent("Config/OK", self, "onConfigSave")
		helpers.bindButtonEvent("Config/Cancel", self, "onConfigCancel")
		helpers.bindButtonEvent("Config/Sound", self, "onSound")
		helpers.bindButtonEvent("Config/Graphics", self, "onGraphics")
		helpers.bindEvent("Config", self, "onConfigCancel", cegui.FrameWindow.EventCloseClicked)
		helpers.bindEvent("Config/Zoom", self, "onZoomChange", cegui.Slider.EventValueChanged)
		helpers.bindEvent("Config/ShowFps", self, "onShowFpsChange", cegui.Checkbox.EventCheckStateChanged)

		helpers.bindEvent("Sound", self, "onSoundCancel", cegui.FrameWindow.EventCloseClicked)
		helpers.bindButtonEvent("Sound/Cancel", self, "onSoundCancel")
		helpers.bindButtonEvent("Sound/OK", self, "onSoundSave")

		helpers.bindEvent("Graphics", self, "onGraphicsCancel", cegui.FrameWindow.EventCloseClicked)
		helpers.bindButtonEvent("Graphics/Cancel", self, "onGraphicsCancel")
		helpers.bindButtonEvent("Graphics/OK", self, "onGraphicsSave")

		helpers.toggleWindow("Config").activate()
		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("Config/Zoom").currentValue = settings.icon_zoom_switch_level
		wm.getWindow("Config/ZoomSpeed").setMaxValue(self.max_zoom_speed)
		wm.getWindow("Config/ZoomSpeed").currentValue = settings.zoom_speed - 1
		wm.getWindow("Config/StarsVisible").setSelected(settings.show_stars_during_icon_view)
		wm.getWindow("Config/ShowFps").setSelected(settings.show_fps)
		wm.getWindow("Config/ShowIntro").setSelected(settings.show_intro)

		helpers.toggleWindow("Config", True)
		helpers.toggleWindow("Sound", False)
		helpers.toggleWindow("Graphics", False)

	def destroy(self):
		wm = cegui.WindowManager.getSingleton()
		wm.destroyWindow(self.config)

	def onShowFpsChange(self, evt):
		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("fps_counter").setVisible(wm.getWindow("Config/ShowFps").isSelected())

	def onZoomChange(self, evt):
		wm = cegui.WindowManager.getSingleton()
		settings.icon_zoom_switch_level = wm.getWindow("Config/Zoom").currentValue

	def onConfigCancel(self, evt):
		self.cleanupGraphics()
		self.cleanupSound()
		self.destroy()

	def onConfigSave(self, evt):
		wm = cegui.WindowManager.getSingleton()
		settings.icon_zoom_switch_level = wm.getWindow("Config/Zoom").currentValue
		settings.show_stars_during_icon_view = wm.getWindow("Config/StarsVisible").isSelected()
		settings.show_fps = wm.getWindow("Config/ShowFps").isSelected()
		settings.show_intro = wm.getWindow("Config/ShowIntro").isSelected()
		zoom_speed = wm.getWindow("Config/ZoomSpeed").currentValue
		settings.zoom_speed = int(zoom_speed) + 1
		self.destroy()

	def onSound(self, evt):
		self.sound_items = []
		dev_win = helpers.setWidgetText("Sound/Driver", settings.current_sound_device)
		for i in range(len(settings.sound_devices)):
			item = cegui.ListboxTextItem(settings.sound_devices[i])
			item.setAutoDeleted(False)
			self.sound_items.append(item)
			dev_win.addItem(item)

		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("Sound/Sound").setSelected(settings.sound_effects)
		wm.getWindow("Sound/Music").setSelected(settings.music)
		helpers.toggleWindow("Sound", True).activate()

	def onGraphics(self, evt):
		wm = cegui.WindowManager.getSingleton()
		if wm.getWindow("Graphics").isVisible():
			return

		self.graphics_items = []
		config = ogre.ConfigFile()
		config.loadDirect("ogre.cfg")
		self.current_system = settings.render_system.getName()
		config_map = settings.render_system.getConfigOptions()
		for c in config_map:
			if c.key == "Video Mode":
				video_modes = c.value.possibleValues
			elif c.key == "Anti aliasing":
				aa = c.value.possibleValues
			elif c.key == "FSAA":
				fsaa = c.value.possibleValues

		full_screen = config.getSetting("Full Screen", self.current_system)
		if full_screen == "Yes":
			self.full_screen = True
			wm.getWindow("Graphics/Fullscreen").setSelected(True)
		else:
			self.full_screen = False
			wm.getWindow("Graphics/Fullscreen").setSelected(False)

		self.video_mode = config.getSetting("Video Mode", self.current_system)
		res_win = helpers.setWidgetText("Graphics/Resolution", self.video_mode)
		for i in range(len(video_modes)):
			item = cegui.ListboxTextItem(video_modes[i])
			item.setAutoDeleted(False)
			self.graphics_items.append(item)
			res_win.addItem(item)

		driver_win = helpers.setWidgetText("Graphics/Driver", self.current_system)
		for value in settings.renderers:
			item = cegui.ListboxTextItem(value.getName())
			item.setAutoDeleted(False)
			self.graphics_items.append(item)
			driver_win.addItem(item)

		# Anti-aliasing comes under different names for opengl and direct3d
		self.fsaa = config.getSetting("FSAA", self.current_system)
		if len(self.fsaa) > 0:
			fsaa_win = helpers.setWidgetText("Graphics/AA", self.fsaa)
			for i in range(len(fsaa)):
				item = cegui.ListboxTextItem(fsaa[i])
				item.setAutoDeleted(False)
				self.graphics_items.append(item)
				fsaa_win.addItem(item)

		self.anti_aliasing = config.getSetting("Anti aliasing", self.current_system)
		if len(self.anti_aliasing) > 0:
			aa_win = helpers.setWidgetText("Graphics/AA", self.anti_aliasing)
			for i in range(len(aa)):
				item = cegui.ListboxTextItem(aa[i])
				item.setAutoDeleted(False)
				self.graphics_items.append(item)
				aa_win.addItem(item)

		helpers.toggleWindow("Graphics", True).activate()

	def onSoundSave(self, evt):
		wm = cegui.WindowManager.getSingleton()
		changed = False
		sound_effects = wm.getWindow("Sound/Sound").isSelected()
		music = wm.getWindow("Sound/Music").isSelected()
		selected_device = wm.getWindow("Sound/Driver").getText()

		if settings.sound_effects != sound_effects:
			settings.sound_effects = sound_effects
			changed = True
			import sound
			if settings.sound_effects is False:
				for sfx in sound.sound_list:
					sfx.stop()
			else:
				for sfx in sound.sound_list:
					sfx.play()
		if settings.music != music:
			settings.music = music
			changed = True
			import sound
			if settings.music is False:
				for sfx in sound.music_list:
					sfx.stop()
			else:
				for sfx in sound.music_list:
					sfx.play()
		if settings.current_sound_device != selected_device:
			changed = True

		if changed:
			def convert(value):
				if value:
					return "Yes"
				else:
					return "No"
			lines = ["Music=%s\n" % convert(music), "Sound=%s\n" % convert(sound_effects)]
			try:
				f = open("sound.cfg", "w")
				f.writelines(lines)
			finally:
				f.close()

		self.cleanupSound()
		helpers.toggleWindow("Sound", False)

	def onSoundCancel(self, evt):
		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("Sound/Sound").setSelected(settings.sound_effects)
		wm.getWindow("Sound/Music").setSelected(settings.music)
		self.cleanupSound()
		helpers.toggleWindow("Sound", False)

	def onGraphicsSave(self, evt):
		changed = False
		wm = cegui.WindowManager.getSingleton()
		full_screen = wm.getWindow("Graphics/Fullscreen").isSelected()
		renderer = wm.getWindow("Graphics/Driver").getText()
		aa = wm.getWindow("Graphics/AA").getText()
		video_mode = wm.getWindow("Graphics/Resolution").getText()

		if self.full_screen != full_screen:
			width = settings.render_window.getWidth()
			height = settings.render_window.getHeight()
			settings.render_window.setFullscreen(full_screen, width, height)
			changed = True
		if self.current_system != renderer:
			changed = True
		if len(self.fsaa) > 0:
			if self.fsaa != aa:
				changed = True
			aa_name = "FSAA"
		if len(self.anti_aliasing) > 0:
			if self.anti_aliasing != aa:
				changed = True
			aa_name = "Anti aliasing"
		if self.video_mode != video_mode:
			changed = True

		renderer = renderer.c_str()
		aa = aa.c_str()
		video_mode = video_mode.c_str()
		print full_screen, renderer, aa, video_mode, aa_name

		if changed:
			try:
				f = open("ogre.cfg", "r")
				lines = f.readlines()
				section_reached = False
				for i in range(len(lines)):
					if lines[i].startswith("\n"):
						continue
					if lines[i].startswith("["):
						name = lines[i].strip("[]\n")
						if self.current_system == name:
							section_reached = True
						else:
							section_reached = False
						continue
					k, v = lines[i].split("=")
					if k == "Render System":
						lines[i] = "%s=%s\n" % (k, renderer)
					elif section_reached:
						if k == "Video Mode":
							lines[i] = "%s=%s\n" % (k, video_mode)
						elif k == "Full Screen":
							if full_screen:
								lines[i] = "%s=Yes\n" % k
							else:
								lines[i] = "%s=No\n" % k
						elif k == aa_name:
							lines[i] = "%s=%s\n" % (k, aa)
			finally:
				f.close()

			try:
				f = open("ogre.cfg", "w")
				f.writelines(lines)
			finally:
				f.close()

		self.cleanupGraphics()
		helpers.toggleWindow("Graphics", False)

	def onGraphicsCancel(self, evt):
		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("Graphics/Fullscreen").setSelected(self.full_screen)
		self.cleanupGraphics()
		helpers.toggleWindow("Graphics", False)

	def cleanupGraphics(self):
		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("Graphics/Driver").setText("")
		wm.getWindow("Graphics/Driver").resetList()
		wm.getWindow("Graphics/Resolution").setText("")
		wm.getWindow("Graphics/Resolution").resetList()
		wm.getWindow("Graphics/AA").setText("")
		wm.getWindow("Graphics/AA").resetList()
		self.graphics_items = []

	def cleanupSound(self):
		wm = cegui.WindowManager.getSingleton()
		wm.getWindow("Sound/Driver").setText("")
		wm.getWindow("Sound/Driver").resetList()
		self.sound_items = []

class MenuWindow(object):
	def __init__(self, parent, window):
		self.parent = parent
		self.menu = helpers.loadWindowLayout("menu.layout")
		window.addChildWindow(self.menu)
		helpers.bindButtonEvent("Menu/Main", self, "onQuitToMain")
		helpers.bindButtonEvent("Menu/Desktop", self, "onQuitToDesktop")
		helpers.bindButtonEvent("Menu/Back", self, "onBack")
		helpers.bindButtonEvent("Menu/Config", self, "onConfig")
		helpers.toggleWindow("Menu", True).activate()

	def destroy(self):
		wm = cegui.WindowManager.getSingleton()
		wm.destroyWindow(self.menu)

	def onConfig(self, evt):
		self.config = ConfigWindow(self.menu)

	def onBack(self, evt):
		self.destroy()

	def onQuitToDesktop(self, evt):
		self.parent.quit()

	def onQuitToMain(self, evt):
		self.destroy()
		self.parent.returnToMain()

