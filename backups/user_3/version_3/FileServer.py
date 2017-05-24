#!/usr/bin/python3.4

import socket
import mysql.connector
import datetime
import sys
import os
import shutil
from passlib.hash import pbkdf2_sha256



class FileServer(object):

	def __init__(self, client_tuple):
		self.client_sock = client_tuple[0]
		self.client_addr = client_tuple[1]
		self.client_ip = self.client_addr[0]

		self.cnx = mysql.connector.connect(user='pysync', password='sesame', host='127.0.0.1', database='pysync_backups')
		self.cursor = self.cnx.cursor()


	def _send_ack(self):
		ack_str = "ACK"
		self.client_sock.send( ack_str.encode() )

	
	def _send_error(self, error_msg):
		error_bytes = error_msg.encode()
		self.client_sock.send(error_bytes)


	def _get_file_name_leaf(self, file_name):
		name_length = len(file_name)
		file_name_list = list(file_name)
		list_pos = name_length - 1
		
		try:
			while ( file_name_list[list_pos] != "/" ):
				list_pos -= 1
			leaf_name = "".join( file_name_list[(list_pos+1):] )
		except IndexError:
			# If the file path does not contain any /, then the leaf name
			#		is just the path itself, so return the input unchanged
			return file_name

		return leaf_name


	def _get_file(self, username):
		filename_bytes = self.client_sock.recv(100)
		filename_str = filename_bytes.decode()
		try:
			self._send_ack()
		except BrokenPipeError:
			return False
		#print('sent ACK for file name ' + filename_str)

		file_size_bytes = self.client_sock.recv(10)
		file_size_str = file_size_bytes.decode()
		
		# HACK: if client disconnected, will get a ValueError here
		#		due to receiving '' over socket
		# Returning False does not make sense considering name
		#		of this function (see comment below about "connected")		
		try:
			file_size = int(file_size_str)
		except ValueError:
			return False
		self._send_ack()
		#print('sent ACK for file size ' + file_size_str)

		query = ('SELECT user_id FROM users WHERE username = %s')
		self.cursor.execute(query, (username,))
		rows_tuple = self.cursor.fetchall()
		user_id = rows_tuple[0][0]

		file_content_bytes = self.client_sock.recv(file_size)
		filename_leaf = self._get_file_name_leaf(filename_str)

		# Versioning: If there are already 3 files with this name in this user's directory,
		#		delete the oldest one
		# HACK: We find the oldest by just deleting the first row encountered (is this robust?)
		query = ('SELECT * FROM files WHERE file_name = %s')
		self.cursor.execute(query, (filename_leaf,))
		self.cursor.fetchall()
		num_rows = self.cursor.rowcount
		if num_rows == 3:
			# move file in version_2 folder to version_1, and version_3 to version_2 
			self._rotate_versions(user_id, filename_leaf)

			# HACK: (see above)
			query = ('DELETE FROM files WHERE file_name = %s LIMIT 1')
			self.cursor.execute(query, (filename_leaf,))
			self.cnx.commit()

			# rotate records in the database
			query = ('UPDATE files \
					  SET version = CASE \
					     WHEN version = 2 THEN 1 \
					     WHEN version = 3 THEN 2 \
					  END \
					  WHERE file_name = %s')
			self.cursor.execute(query, (filename_leaf,))
			self.cnx.commit() 

			version = 3
		else:
			version = num_rows + 1

		dest_prefix = 'backups/user_' + str(user_id) + '/version_' + str(version) + '/'
		output_file = open(dest_prefix + filename_leaf, "wb")
		output_file.write(file_content_bytes)
		output_file.close()

		mod_time_str = datetime.datetime.now()		
		query = ("INSERT INTO files VALUES (%s, %s, %s, %s)")
		self.cursor.execute(query, (user_id, filename_leaf, mod_time_str, version))
		self.cnx.commit()
		self._send_ack()
		print('uploaded file "' + filename_leaf + '" for user ' + username + ' (user_id ==  ' + str(user_id) + ')')
		return True


	def _rotate_versions(self, user_id, filename_leaf):
		os.remove('backups/user_' + str(user_id) + '/version_1/' + filename_leaf)
		shutil.move('backups/user_' + str(user_id) + '/version_2/' + filename_leaf,
					'backups/user_' + str(user_id) + '/version_1/' + filename_leaf)
		shutil.move('backups/user_' + str(user_id) + '/version_3/' + filename_leaf,
					'backups/user_' + str(user_id) + '/version_2/' + filename_leaf)


	def _get_files_from_client(self, username):
		# HACK: returning "connected" does not really make sense considering
		#		name of the function
		connected = True		
		while connected:
			connected = self._get_file(username)			
 

	def _register_account(self):
		username_bytes = self.client_sock.recv(10)
		username_str = username_bytes.decode()
		self._send_ack()
		password_bytes = self.client_sock.recv(10)
		password_str = password_bytes.decode()
		self._send_ack()

		hashed_password = pbkdf2_sha256.hash(password_str)
		
		query = ('INSERT INTO users VALUES (%s, %s, %s)')
		try:
			self.cursor.execute(query, ('NULL', username_str, hashed_password))
		except mysql.connector.errors.IntegrityError:
			print('INTEGRITY ERROR: user tried to register an existent username')
			self._send_error('username ' + username_str + ' already exists')
			return -1

		self.cnx.commit()
		print('registered account with username ' + username_str)
		query = ('SELECT user_id FROM users WHERE username = %s')
		self.cursor.execute(query, (username_str,))
		rows_tuple = self.cursor.fetchall()
		user_id = rows_tuple[0][0]
		
		os.mkdir('backups/user_' + str(user_id))
		for version in [1, 2, 3]:
			os.mkdir('backups/user_' + str(user_id) + '/version_' + str(version))
		
		self._send_ack()
		return 0

	
	def _do_login_challenge(self):
		username_bytes = self.client_sock.recv(10)
		username_str = username_bytes.decode()
		self._send_ack()
		password_bytes = self.client_sock.recv(10)
		password_str = password_bytes.decode()
		self._send_ack()
		
		query = ('SELECT password FROM users WHERE username = %s')
		self.cursor.execute(query, (username_str,))
		rows_tuple = self.cursor.fetchall()
		if not rows_tuple:
			# no such username
			print('failed login with username = ' + username_str + ', password = ' + password_str)
			self._send_error('invalid credentials')
			return None

		hashed_password = rows_tuple[0][0]

		password_correct = pbkdf2_sha256.verify(password_str, hashed_password)
			
		if password_correct:
			print('user ' + username_str + ' logged in')
			self._send_ack()
			return username_str
		else:
			print('failed login with username = ' + username_str + ', password = ' + password_str)
			self._send_error('invalid credentials')
			return None

	
	def _show_user_files(self, username):
		query = ('SELECT user_id FROM users WHERE username = %s')
		self.cursor.execute(query, (username,))
		rows_list = self.cursor.fetchall()
		user_id = 0				
		for row in rows_list:
			user_id = row[0]
			break

		result_str = ""
		query = ('SELECT file_name FROM files WHERE user_id = %s')
		self.cursor.execute(query, (user_id,))
		rows_list = self.cursor.fetchall()
		for row in rows_list:
			result_str += '   ' + row[0] + '\n'
		
		result_bytes = result_str.encode()
		self.client_sock.send(result_bytes)


	def _do_user_request(self, username):
			request_bytes = self.client_sock.recv(5)
			request_str = request_bytes.decode()
			self._send_ack()			
			print('got request ' + request_str + ' from user ' + username)

			if request_str == 'UPL':
				self._get_file(username)
			elif request_str == 'FILES':
				self._show_user_files(username)
			else:
				print('received an unknown request "' + request_str + '" from user ' + username)


	def process_client(self):
		print("got connection from " + self.client_ip)
		self._send_ack()

		user_choice_bytes = self.client_sock.recv(1)
		self._send_ack()
		user_choice_str = user_choice_bytes.decode()

		if (user_choice_str == 'A'):
			username = self._do_login_challenge()
			if username is not None:
				self._get_files_from_client(username)
		elif (user_choice_str == 'L'):
			username = self._do_login_challenge()
			if username is not None:
				self._do_user_request(username)	
		elif (user_choice_str == 'C'):
			self._register_account()
		else:
			print('ERROR in _process_client(): received garbled user choice "' + user_choice_str + '"')
			exit(1)




def main():

	server_ip = '10.0.0.12'		
	server_port = 1234		
	server_sock = socket.socket()
	server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	server_sock.bind( (server_ip, server_port) )
	server_sock.listen(5)

	while(True):
		client_tuple = server_sock.accept()
		server_instance = FileServer(client_tuple)
		server_instance.process_client()


main()


