#!/usr/bin/env python3

from ObliviousTransfer import One_out_of_Two

secret = 1
bob = One_out_of_Two()

secret = bob.start()
print(secret)