#!/usr/bin/python3.4

import os
import sys
import socket
import autoclient

class AuthClient(object):

	def __init__(self, server_ip, server_port):
		self.server_ip = server_ip
		self.server_port = server_port
		self.sock = None
		self.server_msg = None

		self.username = None
		self.password = None

		
	def config_file_exists(self):
		if os.path.isfile('pysync.conf'):
			return 1
		else:
			return 0


	def create_account(self):
		self.username = input("Choose a username: ")
		self.password = input("Choose a password: ")

		self._register_account()


	def send_message(self, msg_str):
		msg_bytes = msg_str.encode()
		self.sock.send(msg_bytes)
		self._get_response()
	

	# receive "ACK" or error message
	def _get_response(self):
		response_bytes = self.sock.recv(100)		
		response_str = response_bytes.decode()
		return response_str 
		

	def _register_account(self):
		
		username_bytes = self.username.encode()		
		self.sock.send(username_bytes)
		self._get_response()
	
		password_bytes = self.password.encode()
		self.sock.send(password_bytes)
		self._get_response()

		self.server_msg = self._get_response()
		if (self.server_msg == "ACK"):
			self._create_config_file()
			print('Finished creating account with username ' + self.username + ', and wrote the config file to current directory')
			exit(0)
		else:
			print('could not create account: got error message "' + self.server_msg + '"')
			exit(1)


	def _create_config_file(self):
		config_file = open('pysync.conf', 'w')
		config_file.write(self.username + '\n')
		config_file.write(self.password + '\n')
		config_file.close()


	def do_login(self):
		
		self.username = input('Enter your username: ')
		username_bytes = self.username.encode()		
		self.sock.send(username_bytes)
		self._get_response()

		self.password = input('Enter your password: ')
		password_bytes = self.password.encode()
		self.sock.send(password_bytes)
		self._get_response()

		self.server_msg = self._get_response()
		if (self.server_msg == "ACK"):
			print('Welcome, ' + self.username + '.')
			return (self.username, self.password, self.sock)
		elif (self.server_msg == 'invalid credentials'):
			print('Incorrect credentials. Please restart and try again, or create an account.')
			exit(1)
		else:
			print('unspecified error when attempting to log in')
			exit(1)


	def _do_auto_login(self):

		config_file = open('pysync.conf', 'r')
		config_lines = []
		for line in config_file:
			stripped_line = line.strip()
			config_lines.append(stripped_line)
		self.username = config_lines[0]
		self.password = config_lines[1]

		username_bytes = self.username.encode()		
		self.sock.send(username_bytes)
		self._get_response()

		password_bytes = self.password.encode()
		self.sock.send(password_bytes)
		self._get_response()

		self.server_msg = self._get_response()
		if (self.server_msg == "ACK"):
			print('automatic login succeeded')
			return self.sock
		elif (self.server_msg == 'invalid credentials'):
			print('pysync client: incorrect credentials in config file (pysync.conf)')
			exit(1)
		else:
			print('pysync client: unspecified error when attempting automatic login')
			exit(1)		
	

	def do_manual_mode(self):
		choice = ' '
		while (choice != 'L' and choice != 'C'):
			choice = input('Do you want to log in (L) or create an account (C)? ').upper()

		self.execute(choice)


	def execute(self, choice):
	
		self.sock = socket.create_connection((self.server_ip, self.server_port))
		self._get_response()	

		if choice == 'A':
			self.send_message('A')
			# HACK: need to separate concerns of execute() from _do_auto_login() ...
			#		the cascading return of the socket to main() makes no sense
			sock = self._do_auto_login()
			return sock
		elif (choice == 'L'):
			self.send_message('L')
			(username, password, sock) = self.do_login()

			file_agent = FileTransactor(username, password, sock)
			option = " "
			while option not in ['U', 'D', 'V', 'Q']:
				option = input('\nDo you want to upload (U), download (D), view (V), or quit (Q)? ').upper()
			if option == 'U':
				file_name = input('specify a file to upload: ')
				file_agent.send_file(file_name)
			elif option == 'D':
				print('specify a file to download: ')
			elif option == 'V':
				file_agent.request_show_files()
			elif option == 'Q':
				print('Goodbye!\n') 
			
		elif (choice == 'C'):
			self.send_message('C')
			self.create_account()	


class FileTransactor(object):

	def __init__(self, username, password, sock):
		self.username = username
		self.password = password
		self.sock = sock


	def send_message(self, msg_str):
		msg_bytes = msg_str.encode()
		self.sock.send(msg_bytes)


	# receive "ACK" or error message
	def _get_response(self):
		response_bytes = self.sock.recv(100)		
		response_str = response_bytes.decode()
		#print('got response ' + response_str)
		return response_str 


	def send_file(self, file_name):
		self.send_message('UPL')
		self._get_response()
		#print('got ACK for upload request')

		self.send_message(file_name)
		self._get_response()
		#print('got ACK for file name ' + file_name)

		file_size_str = str(os.path.getsize(file_name))
		self.send_message(file_size_str)
		self._get_response()
		#print('got ACK for file size ' + file_size_str)

		file_to_upload = open( file_name, "rb" )
		file_bytes = file_to_upload.read()
		file_to_upload.close()

		self.sock.send( file_bytes )
		self._get_response
		print('\nuploaded ' + file_name)


	def request_show_files(self):
		self.send_message('FILES')
		self._get_response()
		server_msg_bytes = self.sock.recv(10000)
		server_msg_string = server_msg_bytes.decode()
		print('\nYour files are:\n' + server_msg_string)



def main():
	
	auth_cli = AuthClient('10.0.0.12', 1234)
	
	if len(sys.argv) < 2:
		if auth_cli.config_file_exists():
			print('config file found ... running in automatic mode')
			sock = auth_cli.execute('A')
			auto_client = autoclient.AutoFileClient(sock)
			auto_client.watch_for_updates(['/home/pysync', '/var/www/php5680'])			
		else:
			print('no config file found ... running in manual mode')
			auth_cli.do_manual_mode()
			sys.exit(0)

	if (sys.argv[1] == '--manage'):
		auth_cli.do_manual_mode()
	else:
		print("pysync client: unrecognized command line option")
	


main()
