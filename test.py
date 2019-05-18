#!/usr/bin/env python3

import math
import random

from andos import tonelli

from Crypto.PublicKey import RSA
from Crypto.Util import number
from Crypto.Random import random

p = 241
q = 769
n = p * q
print(p,q,n)

x = random.randint(0,n)
c = (x*x) % n
print("x", x, "c", c)

tp = tonelli(c,p)
tq = tonelli(c,q)
all_x = [tp, tq, p-tp, q-tq]
print("x1 => all_x", all_x)

x1 = all_x[random.randint(0,3)]
print(math.gcd(x-x1,n))