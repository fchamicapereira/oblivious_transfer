#!/usr/bin/env python3

import socket

from Crypto.PublicKey import RSA
from Crypto.Util import number
from Crypto.Random import random

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

class OT():

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

