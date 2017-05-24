#!/usr/bin/python3.4

import mysql.connector
import sys
from passlib.hash import pbkdf2_sha256

class AccountCreator(object):


	def __init__(self, username, password):
		self.username = username
		self.password = password
		self.cnx = mysql.connector.connect(user='pysync', password='sesame', host='localhost', database='pysync_backups')
		self.cursor = self.cnx.cursor()


	def validate_input(self):
		if (len(self.username) > 10):
			# return "username too long" code to PHP
			#    (return code 1 corresponds to "no arguments" exception, until we handle that)
			sys.exit(2)
		if (len(self.password) > 10):
			# return "password too long" code to PHP
			sys.exit(3)

		# check whether username already exists
		query = ('SELECT username FROM users WHERE username = %s')
		self.cursor.execute(query, (self.username,))
		# have to call fetchall() to avoid "unread result" exception?
		rows_tuple = self.cursor.fetchall()
		num_rows = self.cursor.rowcount
		if num_rows > 0:
			# return "username already exists" code to PHP
			sys.exit(4)


	def create_account(self):
		hashed_password = pbkdf2_sha256.hash(self.password)
		print(hashed_password)

		query = 'INSERT INTO users VALUES (NULL, %s, %s)'
		self.cursor.execute(query, (self.username, hashed_password))
		self.cnx.commit()
		# return "success" code to PHP
		sys.exit(0)



def main():

	username = sys.argv[1]
	password = sys.argv[2]

	acct_creator = AccountCreator(username, password)

	acct_creator.validate_input()
	acct_creator.create_account()


main()
