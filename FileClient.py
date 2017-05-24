#!/usr/bin/python3.4

import os
import socket


class FileClient(object):

	server_ip = '10.0.0.12'
	server_port = 1234

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
		self.set_file( file_name )
		file_name_leaf = self.get_file_name_leaf( file_name )

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
		num_files_str = str(num_files)
		
		self.sock = socket.create_connection( (self.server_ip, self.server_port) )

		self.sock.send( num_files_str.encode() )
		self.get_ack()
		#print("got ACK for number of files")

		file_array_ctr = 0
		while (file_array_ctr < num_files):
			self.send_file( file_list[file_array_ctr] )
			file_array_ctr += 1

		
		


def main():
	
	client = FileClient()
	client.send_files_to_server( ['/home/ian/des/go.sh', '/home/ian/des/decrypt.cpp', '/home/ian/des/encrypt.cpp'] )


main()
