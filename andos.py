#!/usr/bin/env python3

import random
import math

"""
	===================================================

	OBLIVIOUS ALL-OR-NOTHING TRANSFER (ANDOS) LIBRARY

	===================================================
"""

def is_quadratic_residue(a, m):
	for b in range(1,int((m - 1) / 2) + 1):
		if (b ** 2) % m == a % m:
			return True
	return False

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

class Server:

	encoding = "utf-8"
	pad_char = "="

	def __init__(self, m, p, q):
		self.m = m
		self.p = p
		self.q = q
		self.y = (p * q) % m

		# TODO: check if p and q are prime ?

		self.Z = [ i for i in range(self.m) ]
		self.Zt = [ i for i in self.Z if math.gcd(i, self.m) == 1 ]

		self.secrets = []
		self.secrets_size = 0 # size of all the secrets (they should all be the same size)

		self.z = []

	def store_secret(self, secret):

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
				self.secrets[i] += (size - self.secrets_size) * pad
			self.secrets_size = size

		# convert to bytes and store
		self.secrets.append(bytes(secret, self.encoding))

	def get_secret(self, i):
		s = self.secrets[i].decode(self.encoding)

		while len(s) > 0 and s[-1:] == self.pad_char:
			s = s[:-1]

		return s

	def get_bit(self, secret_index, bit_index):
		return (int.from_bytes(self.secrets[secret_index], "big") >> bit_index) & 1

	def validate_sigma_packets(self, sigma_packets):
		pass

	def respond(self, sigma_packets, requested_secret):
		self.validate_sigma_packets(sigma_packets)

		packet = sigma_packets[requested_secret]




	def start(self):
		def compute_z():
			for word in range(len(self.secrets)):
				self.z.append([])

				for index in range(self.secrets_size * 8):
					x = self.Zt[random.randint(0, len(self.Zt) - 1)]
					z = ( x*x * int(math.pow(self.y, self.get_bit(word, index))) ) % self.m

					self.z[word].append(z)

		compute_z()

class Client:

	def __init__(self, z, m, y):
		self.z = z
		self.m = m
		self.y = y

		self.Z = [ i for i in range(self.m) ]
		self.Zt = [ i for i in self.Z if math.gcd(i, self.m) == 1 ]

	def request_secret(self, i):

		sigma = [ i for i in range(len(z)) ]
		random.shuffle(sigma)
		sigma_packets = []

		for secret_index in range(len(self.z)):
				sigma_packets.append([])

				for index in range(len(self.z[secret_index])):
					a = random.randint(0, 1)
					r = self.Zt[random.randint(0, len(self.Zt) - 1)]

					sigma_packets[secret_index].append( (z[sigma[secret_index]][index] * r*r * int(math.pow(self.y, a))) % self.m )

		# TODO: convince Alice that sigma permutated is valid

		return sigma_packets

s = Server(134, 2333, 2719)

s.store_secret("A")
s.store_secret("B")

s.start()

# client
z = s.z
m = s.m
y = s.y

c = Client(z, m, y)
print(c.request_secret(0))

