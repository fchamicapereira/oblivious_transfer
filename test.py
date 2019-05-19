#!/usr/bin/env python3

from threading import Thread
import time
from ObliviousTransfer import One_out_of_Two
import random

port = 8000

class Alice(Thread):
	def run(self):
		alice = One_out_of_Two()

		alice.store_secret("They SEE things", "NSA leak")
		alice.store_secret("He doesn't see anything", "Trump leak")

		alice.show_secrets()

		alice.start(port=port)

class Bob(Thread):
	def run(self):
		bob = One_out_of_Two()
		time.sleep(2)
		bob.connect(port=port)

while True:
	try:
		alice = Alice()
		bob = Bob()

		port = random.randint(8000, 9000)
		print("port", port)

		alice.start()
		bob.start()
		alice.join()
		bob.join()
	except ValueError:
		print("EXCEPTION")
		alice.join()
		bob.join()
		break
	except ConnectionResetError:
		print("EXCEPTION")
		alice.join()
		bob.join()
		break