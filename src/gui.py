import ogre.gui.CEGUI as cegui

from tp.netlib.objects import OrderDescs
from tp.netlib.objects.constants import *

import helpers

ARG_GUI_MAP = {
		ARG_ABS_COORD:'Position',
		ARG_TIME:'Turns',
		ARG_LIST:'List',
		ARG_STRING:'String',
		ARG_OBJECT:'Objects',
		}

class MessageWindow(object):
	def __init__(self, parent):
		self.messages = []
		self.message_index = 0
		self.goto_index = 0
		self.parent = parent

		helpers.bindEvent("Messages/Next", self, "nextMessage", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Prev", self, "prevMessage", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Goto", self, "gotoMessageSubject", cegui.PushButton.EventClicked)
		helpers.bindEvent("Messages/Delete", self, "deleteMessage", cegui.PushButton.EventClicked)

	def create(self, cache):
		for val in cache.messages[0]:
			self.messages.append(val)

		if len(self.messages) > 0:
			if len(self.messages) > self.message_index:
				self.setCurrentMessage(self.messages[self.message_index])
			else:
				self.setCurrentMessage(self.messages[0])

	def nextMessage(self, evt):
		"""Sets messagebox to the next message if available"""
		if len(self.messages) > 0 and self.message_index < len(self.messages) - 1:
			self.message_index += 1
			self.goto_index = 0
			self.setCurrentMessage(self.messages[self.message_index])

	def prevMessage(self, evt):
		"""Sets messagebox to the previous message if available"""
		if len(self.messages) > 0 and self.message_index > 0:
			self.message_index -= 1
			self.goto_index = 0
			self.setCurrentMessage(self.messages[self.message_index])

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
			if reference[0] is OBJECT:
				id = reference[1]
				if id is 1: # universe
					continue
				if i < self.goto_index + 1:
					continue
				if self.selectObjectById(id):
					self.parent.starmap.center(id)
					self.goto_index = i
					break

	def setCurrentMessage(self, message_object):
		"""Sets message text inside message window"""
		message = message_object.CurrentOrder
		text = "Subject: " + message.subject + "\n"
		text += "\n"
		text += message.body
		helpers.setWidgetText("Messages/Message", text)

class ArgumentsWindow(object):
	def __init__(self, parent):
		self.arguments = []
		self.arguments_pending_update = []
		self.parent = parent
		self.id = None
		self.order_subtype = None

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
		helpers.toggleWindow("Arguments", False)
		print self.arguments
		for arg in self.arguments:
			cegui.WindowManager.getSingleton().destroyWindow(arg)
		self.arguments = []
		self.arguments_pending_update = []
		self.order_subtype = None
		self.id = None

	def confirm(self, evt):
		print "Sending Order"
		wm = cegui.WindowManager.getSingleton()

		order_description = OrderDescs()[self.order_subtype]
		print order_description
		orderargs = [0, self.id, -1, order_description.subtype, 0, []]

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
				# FIXME
				value = [(long(elem_widget.text.c_str()), 100)]
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
				# FIXME
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
						return
				value = [long(text)]
			else:
				self.hide()
				return

			orderargs += value

		order = order_description(*orderargs)
		self.parent.sendOrder(self.id, order, "change")
		self.hide()

	def show(self, name):
		wm = cegui.WindowManager.getSingleton()
		args = wm.getWindow("Arguments")
		args.show()
		args.activate()
		args.text = name

	def setCurrentOrder(self, id, order_subtype):
		self.id = id
		self.order_subtype = order_subtype

	def addArgument(self, caption, argument):
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
			list_widget = wm.getWindow("Argument%i/%s/Object" % prefix)
			for id, obj in self.parent.objects.items():
				item = cegui.ListboxTextItem("%s (%i)" % (obj.name, id))
				print item.text
				item.setAutoDeleted(False)
				if prefix in self.object_list:
					self.object_list[prefix].append(item)
				else:
					self.object_list[prefix] = [item]
				list_widget.addItem(item)

		offset_x = cegui.UDim(0, 0)
		offset_y = cegui.UDim(0, 0)
		for arg_widget in self.arguments:
			offset_y += arg_widget.position.d_y + arg_widget.height
		widget.position += cegui.UVector2(offset_x, offset_y)
		self.arguments.append(widget)

		return widget

	def addItemToList(self, evt):
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
							if item.text.c_str() == selection_name:
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

	def update(self):
		#print "Updating list items"
		if self.id != None and self.order_subtype != None:
			order = self.parent.getCache().orders[self.id].last.CurrentOrder
			for triplet in self.arguments_pending_update:
				#print triplet
				arg_type = triplet[0]
				argument = triplet[1]
				attribute = triplet[2]

				if arg_type is ARG_LIST:
					update_list = getattr(order, attribute)[0]
					selection = argument.getChild("%s/Selection" % argument.name)
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

