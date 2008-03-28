
from xstruct import pack

from Header import Processed

class TimeRemaining(Processed):
	"""\
	The TimeRemaining packet consists of:
		* UInt32, Seconds left till the turn ends.
	"""
	no = 15
	struct = "j"

	def __init__(self, sequence, time):
		Processed.__init__(self, sequence)

		# Length is:
		#  * 4 bytes UInt32
		#
		self.length = 4
		self.time = time
	
	def __str__(self):
		output = Processed.__str__(self)
		output += pack(self.struct, self.time)

		return output
