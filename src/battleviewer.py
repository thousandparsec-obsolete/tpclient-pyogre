#! /usr/bin/env python

import optparse

from battlemanager import BattleManager

if __name__ == '__main__':
	parser = optparse.OptionParser()
	parser.add_option("-f", "--file", dest="filename", help="BattleXML file to read from",
			metavar="FILE", default="battlexml/example1.xml")
	(options, args) = parser.parse_args()
	app = BattleManager(options.filename)
	app.go()
	app.Cleanup()
