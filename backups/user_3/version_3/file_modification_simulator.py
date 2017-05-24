#!/usr/bin/python3.4

import os, sys
import subprocess
import time


def main():
	
	# wait until ~5 seconds after start of watchForUpdates() before "saving" bar_3
	time.sleep(10)

	# "save" bar_3 with modified time = Apr 13 2020
		# try/except is a workaround for a failed call after tearDown()
	try:
		os.utime( path = "./test_dir/bar_3", times = (1586775521.0021467, 1586775521.0021467) )
	except FileNotFoundError:
		sys.exit(0)


main()
