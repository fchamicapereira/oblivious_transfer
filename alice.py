#!/usr/bin/env python3

from andos import OT

secret = 1
alice = OT(secret)

alice.start()