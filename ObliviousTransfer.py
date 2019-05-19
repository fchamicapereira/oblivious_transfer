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

keySize = 1024

def legendre(a, p):
	return pow(a, (p - 1) // 2, p)

def tonelli(n, p):
	assert legendre(n, p) == 1, "not a square (mod p)"
	q = p - 1
	s = 0
	while q % 2 == 0:
		q //= 2
		s += 1
	if s == 1:
		return pow(n, (p + 1) // 4, p)
	for z in range(2, p):
		if p - 1 == legendre(z, p):
			break
	c = pow(z, q, p)
	r = pow(n, (q + 1) // 2, p)
	t = pow(n, q, p)
	m = s
	t2 = 0
	while (t - 1) % p != 0:
		t2 = (t * t) % p
		for i in range(1, m):
			if (t2 - 1) % p == 0:
				break
			t2 = (t2 * t2) % p
		b = pow(c, 1 << (m - i - 1), p)
		r = (r * b) % p
		c = (b * b) % p
		t = (t * c) % p
		m = i
	return r

class ANDOS():

	pad = chr(0x00)

	def __init__(self, secret):
		self.secret = secret

		print("Generating Ka...")
		self.Ka = RSA.generate(keySize)
		print("Done")

		print("Genering primes p, q...")
		self.p = number.getPrime(keySize)
		self.q = number.getPrime(keySize)
		self.n = self.p * self.q
		print("Done")

		print(self.p, self.q)

	def recvN(self, conn):
		n = int.from_bytes(conn.recv(keySize), "little")

		x = random.randint(0, n)
		c = (x * x) % n

		conn.sendall(c.to_bytes(keySize, "little"))

		x1 = int.from_bytes(conn.recv(keySize), "little")

		d = number.GCD(x - x1, n)
		# d = p or d = q (of the other user) with 1/2 probability

		# checking factorization
		if d != 1 and n % d == 0:
			p = d
			q = n // d

			return (0, p, q)
			
		return (1, 0, 0)

	def sendN(self, conn):
		conn.sendall(self.n.to_bytes(keySize, "little"))

		c = int.from_bytes(conn.recv(keySize), "little")

		# sending a square root of c mod n
		root_p = tonelli(c,self.p)
		root_q = tonelli(c, self.q)

		roots = [ root_p, self.p - root_p, root_q, self.q - root_q ]
		x1 = roots[random.randint(0,3)]

		conn.sendall(x1.to_bytes(keySize, "little"))
	
	def sendEpsilon(self, conn, knowledge, secret):
		epsilon = (knowledge ^ self.secret).to_bytes(1, "little")
		conn.sendall(epsilon, 1)
	
	def recvEpsilon(self, conn):
		return conn.recv(1)

	def start(self, host="localhost", port=8888):

		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.bind((host, port))
			s.listen()
			conn, addr = s.accept()

			with conn:
				self.sendN(conn)
				result = self.recvN(conn)
				
				print(result)

				self.sendEpsilon(conn, result[0], self.secret)
				other_epsilon = int.from_bytes(self.recvEpsilon(conn), "little")

				print(other_epsilon)

	def connect(self, host="localhost", port=8888):
		
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			s.connect((host, port))

			result = self.recvN(s)
			self.sendN(s)

			print(result)

			other_epsilon = int.from_bytes(self.recvEpsilon(s), "little")
			self.sendEpsilon(s, result[0], secret)

			print(other_epsilon)

class One_out_of_Two():
	
	encoding = "utf-8"
	pad_char = "="

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

			print(description, secret, sep=": ")

	def sendInt(self, conn, integer):
		print("sending", integer)
		conn.sendall(bytes(str(integer), self.encoding))
		conn.recv(1)
		print("done")

	def recvInt(self, conn):
		integer = conn.recv(keySize).decode(self.encoding)
		conn.sendall(bytes(1))
		print("received", integer)

		return int(integer)

	def start(self, host="localhost", port=8883):

		def listen():

			x = [
				[ random.randint(0, self.n) for i in range(keySize) ],
				[ random.randint(0, self.n) for i in range(self.secrets_size) ]
				]

			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
				s.bind((host, port))
				s.listen()
				conn, addr = s.accept()

				with conn:
					conn.sendall(self.secrets_size.to_bytes(8, "little"))

					conn.sendall(self.n.to_bytes(keySize, "little"))
					conn.sendall(self.e.to_bytes(keySize, "little"))

					for i in range(2):
						for b in range(self.secrets_size):
							self.sendInt(conn, x[i][b])

					v = [ 0 for i in range(self.secrets_size) ]

					for b in range(self.secrets_size):
						v[b] = self.recvInt(conn)

					k = [ [ 0 for i in range(self.secrets_size) ], [ 0 for i in range(self.secrets_size) ] ]
					m = [ [ 0 for i in range(self.secrets_size) ], [ 0 for i in range(self.secrets_size) ] ]


					for i in range(2):
						print("sending m'", i)

						for b in range(self.secrets_size):
							vb = v[b]
							xb = x[i][b]
							mb = self.secrets[i]["secret"][b]

							k[i][b] = pow(vb - xb, self.d, self.n)
							m[i][b] = k[i][b] ^ mb
						
							self.sendInt(conn, m[i][b])
					
		def connect():
			
			with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as conn:
				conn.connect((host, port))

				self.secrets_size = int.from_bytes(conn.recv(8), "little")

				n = int.from_bytes(conn.recv(keySize), "little")
				e = int.from_bytes(conn.recv(keySize), "little")

				x = [ [ 0 for i in range(self.secrets_size) ], [ 0 for i in range(self.secrets_size) ] ]

				for j in range(2):
					for i in range(self.secrets_size):
						x[j][i] = self.recvInt(conn)

				k = [ random.randint(0, n) for i in range(self.secrets_size) ]

				#input
				b = 0

				# encrypt
				for i in range(self.secrets_size):
					kb = k[i]
					xb = x[b][i]

					self.sendInt(conn, (xb + pow(kb, e, n)) % n)

				m = bytearray(bytes(self.secrets_size))

				#decrypt
				for j in range(2):

					for i in range(self.secrets_size):
						mb = self.recvInt(conn)

						# this is the message we want to receive
						if j == b:
							kb = k[i]
							
							print("kb", kb)
							print("mb", mb)
							print("kb xor mb", mb ^kb)

							m[i] = mb ^ kb

				secret = bytes(m)
				return self.parse_secret(secret)

		if self.client:
			return connect()
		else:
			listen()
