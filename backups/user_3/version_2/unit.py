#!/usr/bin/python3.4

import unittest
import os, sys
import time
import subprocess 


def getDirectoryFiles(single_directory_string):

	list_of_files = os.listdir( single_directory_string )

	list_of_full_paths = []
	absolute_path = None
	for file_name in list_of_files:
		absolute_path = os.path.join( single_directory_string, file_name )
		list_of_full_paths.append( absolute_path )
	
	list_of_full_paths.sort()
	return list_of_full_paths


def getModifiedTimes(list_of_files):

	list_of_modified_times = []
	modified_time = None
	for file_path in list_of_files:
		modified_time = os.path.getmtime( file_path )
		list_of_modified_times.append( modified_time )

	return list_of_modified_times


def getMultipleDirectoriesFiles( list_of_directories ):

	flat_list_of_files = []
	for directory in list_of_directories:
		flat_list_of_files += getDirectoryFiles( directory )

	return flat_list_of_files


def getMultiDirectoriesTimes( list_of_directories ):

	list_of_files = getMultipleDirectoriesFiles( list_of_directories )
	list_of_times = getModifiedTimes( list_of_files )
	
	return list_of_times


def makeFileTimeDict( list_of_directories ):

	list_of_files = getMultipleDirectoriesFiles( list_of_directories )
	list_of_times = getMultiDirectoriesTimes( list_of_directories )

	file_time_dict = {}
	file_time = None
	counter = 0
	for some_file in list_of_files:
		file_time = list_of_times[ counter ]
		file_time_dict[ some_file ] = file_time
		counter += 1 

	return file_time_dict 
 

def watchForUpdates( list_of_directories ): 

	old_file_time_dict = {}	 
	new_file_time_dict = {}
	cycles = 0
	# for unit testing, only try three update cycles before giving up 
	while(cycles < 3):
		time.sleep(5)
		
		new_file_time_dict = makeFileTimeDict( list_of_directories )
		file_names_list = new_file_time_dict.keys()
		for file_name in file_names_list:
			try:
				if new_file_time_dict[ file_name ] > old_file_time_dict[ file_name ]:
					# WARNING: "omitting directory" error should be dealt with (instead of 2> redirect)
					
					# in production, do not test for this particular file, and do not return
					if (file_name == "./test_dir/bar_3"):
						subprocess.call( "cp " + file_name + " ./modified_files_dir 2> /dev/null", shell=True )
						return   

			except KeyError:
					# if a new file is found, back it up and add it to the old dict
					# in production, do not test for this particular file, and do not return
					if (file_name == "./test_dir/bar_3"):
						subprocess.call( "cp " + file_name + " ./modified_files_dir 2> /dev/null", shell=True )
						return
					
					old_file_time_dict[ file_name ] = new_file_time_dict[ file_name ]
		
		old_file_time_dict = new_file_time_dict
		cycles += 1		# for unit testing only



class myTest(unittest.TestCase): 

	def setUp(self):

		# make test folders and files
		os.mkdir("./test_dir")
		os.mkdir("./test_dir_2")
		subprocess.call("touch ./test_dir/bar_1.xslx ./test_dir/foo_1.txt", shell=True)
		os.utime( path = "./test_dir/bar_1.xslx", times = (1286775521.0021467, 1286775521.0021467) )
		os.utime( path = "./test_dir/foo_1.txt", times = (1286775521.0021467, 1286775521.0021467) )
		subprocess.call("touch ./test_dir_2/bar_2.xslx ./test_dir_2/foo_2.txt", shell=True)
		os.utime( path = "./test_dir_2/bar_2.xslx", times = (1486775521.0021467, 1486775521.0021467) )
		os.utime( path = "./test_dir_2/foo_2.txt", times = (1486775521.0021467, 1486775521.0021467) )


	def test_get_directory_files(self):
		# get sorted list of files (including directories) from a directory
		#	(with full paths)

		# setup

		# test
		self.assertEqual( ["./test_dir/bar_1.xslx", "./test_dir/foo_1.txt"],  getDirectoryFiles("./test_dir") )

	def test_get_modified_times(self):
		# get a list of "last modified" timestamps for a list of files
		#	(index of each timestamp matches corresponding file index
		#	 in the input list)
		
		# setup
		list_of_files = getDirectoryFiles("./test_dir")

		# test
		# WARNING: floating point comparison problem in least significant digit, 
		#	e.g. (1486775521.0021467 == 1486775521.0021468) passes
		self.assertEqual( [1286775521.0021467, 1286775521.0021467], getModifiedTimes( list_of_files ) )

	def test_get_multiple_directories_files(self):
		# get a list of absolute file paths from a specified list of directories

		# setup
		list_of_directories = ["./test_dir", "./test_dir_2"]
		test_flat_list_of_files = ["./test_dir/bar_1.xslx", "./test_dir/foo_1.txt", 
							  	   "./test_dir_2/bar_2.xslx", "./test_dir_2/foo_2.txt"]

		# test
		returned_flat_list_of_files = getMultipleDirectoriesFiles( list_of_directories )
		self.assertEqual( returned_flat_list_of_files, test_flat_list_of_files )

	def test_get_initial_times(self):
		# get the initial modified times for all the files in a list of directories

		# setup
		list_of_directories = ["./test_dir", "./test_dir_2"]

		# test
		list_of_times = getMultiDirectoriesTimes( list_of_directories )
		
		# WARNING: floating point comparison problem in least significant digit
		self.assertEqual( [1286775521.0021467, 1286775521.0021467, 1486775521.0021467, 1486775521.0021467], list_of_times )

	def test_make_file_time_dict(self):
		# make a dictionary associating file names with last modified times

		# setup
		list_of_directories = ["./test_dir", "./test_dir_2"]

		# test
		file_time_dict = makeFileTimeDict( list_of_directories )
		self.assertEqual( file_time_dict, {'./test_dir/bar_1.xslx': 1286775521.0021467,
  										   './test_dir/foo_1.txt': 1286775521.0021467,
										   './test_dir_2/bar_2.xslx': 1486775521.0021467,
										   './test_dir_2/foo_2.txt': 1486775521.0021467} )


	def tearDown(self):

		# delete test folders and their contents
		subprocess.call("rm -rf ./test_dir ./test_dir_2", shell=True)
		


	def test_watch_for_updates(self):
		# watch for changes in file modified times

		# setup
		list_of_directories = ["./test_dir", "./test_dir_2"]	
		os.mkdir("./modified_files_dir")

		# test
		
		subprocess.call("touch ./test_dir/bar_3", shell=True)
		
			# start separate process to simulate a user saving files
			# this process will modify bar_3 for the subsequent test
		subprocess.call("file_modification_simulator.py &", shell=True)

		watchForUpdates( list_of_directories )
		modified_files = getDirectoryFiles( "./modified_files_dir" )
		self.assertEqual( modified_files, ["./modified_files_dir/bar_3"] )

		#teardown
		subprocess.call("rm -rf ./modified_files_dir", shell=True)


if __name__ == "__main__":
	unittest.main()
