#!/usr/bin/python3.4

from passlib.hash import pbkdf2_sha256
import mysql.connector
import sys


def main():
	username = sys.argv[1]
	candidate_password = sys.argv[2]
	
	cnx = mysql.connector.connect(user='pysync', password='sesame', host='localhost', database='pysync_backups')
	cursor = cnx.cursor()
	query = ('SELECT password FROM users WHERE username = %s')
	cursor.execute(query, (username,))
	rows_tuple = cursor.fetchall()

	if not rows_tuple:
		# no such username
		sys.exit(72)

	hashed_password = rows_tuple[0][0]		
	password_matches = pbkdf2_sha256.verify(candidate_password, hashed_password)
	if not password_matches:
		sys.exit(37)
	else:
		sys.exit(0)



main()
