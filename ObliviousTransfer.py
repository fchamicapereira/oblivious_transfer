#!/usr/bin/env python3

"""
	===================================================

	OBLIVIOUS TRANSFER LIBRARY

	Contains:
		1-out-of-2 oblivious transfer

	===================================================
"""

import socket

from Crypto.PublicKey import RSA
from Crypto.Util import number
from Crypto.Random import random, get_random_bytes

PORT = 8881
keySize = 1024

class One_out_of_Two():
	
	encoding = "utf-8"
	pad_char = chr(0x00)

	def __init__(self, client=True):

		self.client = client

		if not self.client:
			print("Generating RSA key pair...")
			K = RSA.generate(keySize)

			self.d = K.d
			self.e = K.e
			self.n = K.n

			print("Done")

			self.secrets = []

		self.secrets_size = 0


	def store_secret(self, secret, description):

		if self.client:
			print("You are a client, you don't store secrets, you discover them.")
			return

		if (len(self.secrets) == 2):
			print("You already stored 2 secrets. That's enough!")
			return

		b = bytes(secret, self.encoding)
		pad = bytes(self.pad_char, self.encoding)

		# all the secrets must have the same size
		# the size should be the size of the longest secret
		# all the others must be padded

		size = len(b)

		if size < self.secrets_size:
			b += (self.secrets_size - size) * pad

		elif size > self.secrets_size:
			for i in range(len(self.secrets)):
				self.secrets[i]["secret"] += (size - self.secrets_size) * pad
			self.secrets_size = size

		# convert to bytes and store
		self.secrets.append({ "description": description, "secret": b })

	def parse_secret(self, secret):
		s = secret.decode(self.encoding)

		while len(s) > 0 and s[-1:] == self.pad_char:
			s = s[:-1]

		return s

	def get_secret(self, i):
		if self.client:
			print("You don't have secret, you are a client.")
			return

		return self.parse_secret(self.secrets[i]["secret"])

	def show_secrets(self):
		if self.client:
			print("You don't have secret, you are a client.")
			return

		for i in range(len(self.secrets)):
			secret = self.get_secret(i)
			description = self.secrets[i]["description"]

			print("\t" + description, secret, sep=": ")

	def askDescriptions(self, host="localhost", port=PORT):

		if not self.client:
			print("You HAVE the secrets, what do you need to ask for?")
			return

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
			conn.connect((host, port))

			# 0 for asking for description, 1 for requesting secret
			conn.send((0).to_bytes(1, "little"))

			descriptions = []
			for i in range(2):
				description_size = int.from_bytes(conn.recv(8), "little")
				descriptions.append(conn.recv(description_size).decode(self.encoding))
			
			return descriptions

	def start(self, host="localhost", port=PORT, choice=0):

		def sendInt(conn, integer):
			conn.sendall(bytes(str(integer), self.encoding))
			conn.recv(1)

		def recvInt(conn):
			integer = conn.recv(keySize).decode(self.encoding)
			conn.sendall(bytes(1))

			return int(integer)

		def listen():

			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.bind((host, port))

				while True:
					s.listen()
					conn, addr = s.accept()

					with conn:
						question = int.from_bytes(conn.recv(1), "little")

						if question == 0:
							#client is asking for description

							for i in range(len(self.secrets)):
								conn.sendall(len(self.secrets[i]["description"]).to_bytes(8, "little"))
								conn.sendall(bytes(self.secrets[i]["description"], self.encoding))
							
							continue
						
						# asking for secret

						print("Generating x0, x1")

						x = [
							[ random.randint(0, self.n) for i in range(keySize) ],
							[ random.randint(0, self.n) for i in range(self.secrets_size) ]
						]

						conn.sendall(self.secrets_size.to_bytes(8, "little"))

						print("Sending N and e")
						conn.sendall(self.n.to_bytes(keySize, "little"))
						conn.sendall(self.e.to_bytes(keySize, "little"))

						print("Sending x0, x1")

						for i in range(2):
							for b in range(self.secrets_size):
								sendInt(conn, x[i][b])

						v = [ 0 for i in range(self.secrets_size) ]

						for b in range(self.secrets_size):
							v[b] = recvInt(conn)

						print("Received v")

						k = [ [ 0 for i in range(self.secrets_size) ], [ 0 for i in range(self.secrets_size) ] ]
						m = [ [ 0 for i in range(self.secrets_size) ], [ 0 for i in range(self.secrets_size) ] ]

						print("Calculating and sending m0', m1'")

						for i in range(2):

							for b in range(self.secrets_size):
								vb = v[b]
								xb = x[i][b]
								mb = self.secrets[i]["secret"][b]

								k[i][b] = pow(vb - xb, self.d, self.n)
								m[i][b] = k[i][b] ^ mb
							
								sendInt(conn, m[i][b])

		def connect():
			
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
				conn.connect((host, port))

				# 0 for asking for description, 1 for requesting secret
				conn.send((1).to_bytes(1, "little"))

				self.secrets_size = int.from_bytes(conn.recv(8), "little")

				n = int.from_bytes(conn.recv(keySize), "little")
				e = int.from_bytes(conn.recv(keySize), "little")

				print("Received N, e")

				x = [ [ 0 for i in range(self.secrets_size) ], [ 0 for i in range(self.secrets_size) ] ]

				for j in range(2):
					for i in range(self.secrets_size):
						x[j][i] = recvInt(conn)

				print("Received x0, x1")

				print("Generating random k")
				k = [ random.randint(0, n) for i in range(self.secrets_size) ]

				#input
				b = choice

				print("Calculating and sending v")

				# encrypt
				for i in range(self.secrets_size):
					kb = k[i]
					xb = x[b][i]

					sendInt(conn, (xb + pow(kb, e, n)) % n)

				m = bytearray(bytes(self.secrets_size))

				print("Receiving m0', m1'")
				#decrypt
				for j in range(2):

					for i in range(self.secrets_size):
						mb = recvInt(conn)

						# this is the message we want to receive
						if j == b:
							kb = k[i]
							
							m[i] = mb ^ kb

				secret = bytes(m)
				return self.parse_secret(secret)

		if self.client:
			return connect()
		else:
			listen()
