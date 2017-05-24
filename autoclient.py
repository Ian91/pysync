#!/usr/bin/python3.4

import unittest
import os, sys
import time
import subprocess
import socket 


class AutoFileClient(object):

	def __init__(self, sock):
		self.sock = sock

	def getDirectoryFiles(self, single_directory_string):

		list_of_files = os.listdir( single_directory_string)

		list_of_full_paths = []
		absolute_path = None
		for file_name in list_of_files:
			absolute_path = os.path.join( single_directory_string, file_name )
			
			# do not include directories
			if not os.path.isdir(absolute_path):
				list_of_full_paths.append( absolute_path )
	
		list_of_full_paths.sort()
		return list_of_full_paths


	def getModifiedTimes(self, list_of_files):

		list_of_modified_times = []
		modified_time = None
		for file_path in list_of_files:
			modified_time = os.path.getmtime( file_path )
			list_of_modified_times.append( modified_time )

		return list_of_modified_times


	def getMultipleDirectoriesFiles(self, list_of_directories):

		flat_list_of_files = []
		for directory in list_of_directories:
			flat_list_of_files += self.getDirectoryFiles( directory )

		return flat_list_of_files


	def getMultiDirectoriesTimes(self, list_of_directories):

		list_of_files = self.getMultipleDirectoriesFiles(list_of_directories)
		list_of_times = self.getModifiedTimes(list_of_files)
	
		return list_of_times


	def makeFileTimeDict(self, list_of_directories):

		list_of_files = self.getMultipleDirectoriesFiles(list_of_directories)
		list_of_times = self.getMultiDirectoriesTimes(list_of_directories)

		file_time_dict = {}
		file_time = None
		counter = 0
		for some_file in list_of_files:
			file_time = list_of_times[ counter ]
			file_time_dict[ some_file ] = file_time
			counter += 1 

		return file_time_dict 
 

	def watch_for_updates(self, list_of_directories): 

		old_file_time_dict = {}	 
		new_file_time_dict = {} 
		while(True):
			time.sleep(10)
		
			new_file_time_dict = self.makeFileTimeDict( list_of_directories )
			file_names_list = new_file_time_dict.keys()
			for file_name in file_names_list:
				try:
					if new_file_time_dict[ file_name ] > old_file_time_dict[ file_name ]:
						self.send_files_to_server([file_name])
						   

				except KeyError:
					# if a new file is found, back it up and add it to the old dict
					self.send_files_to_server( [file_name] )
					old_file_time_dict[ file_name ] = new_file_time_dict[ file_name ]
		
			old_file_time_dict = new_file_time_dict


	def get_ack(self):
		self.sock.recv(5)

	def set_file(self, file_path):		
		self.file_name = file_path
		self.file_size = os.path.getsize(self.file_name)
		self.file_size_str = str(self.file_size)

	
	def get_file_name_leaf(self, file_name):
		name_length = len(file_name)
		file_name_list = list(file_name)
		list_pos = name_length - 1
		
		while ( file_name_list[list_pos] != "/" ):
			list_pos -= 1
		leaf_name = "".join( file_name_list[(list_pos+1):] )

		return leaf_name				


	def	send_file(self, file_name):
		# NOTE: remove this 'leaf' functionality after backup subdirectories
		#		are implemented
		self.set_file(file_name)
		file_name_leaf = self.get_file_name_leaf(file_name)

		self.sock.send( file_name_leaf.encode() )
		self.get_ack()
		#print("got ACK for name of " + file_name_leaf)

		#print("file " + file_name + " has size " + self.file_size_str)
		self.sock.send( self.file_size_str.encode() )
		self.get_ack()
		#print("got ACK for size of file " + file_name_leaf)

		input_file = open( file_name, "rb" )
		file_bytes = input_file.read()
		input_file.close()

		self.sock.send( file_bytes )
		self.get_ack()
		#print("got ACK for sending file " + file_name_leaf)

		
	def send_files_to_server(self, file_list):
		num_files = len(file_list)
		file_array_ctr = 0
		while (file_array_ctr < num_files):
			self.send_file(file_list[file_array_ctr])
			file_array_ctr += 1




def main():
	auto_client = AutoFileClient()	
	auto_client.watch_for_updates(["/home/ian/des_fast", "/home/ian/set"])

if __name__ == "__main__":
	main()
