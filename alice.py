#!/usr/bin/env python3

from ObliviousTransfer import One_out_of_Two

secret = 1
alice = One_out_of_Two(client=False)

alice.store_secret("They SEE things", "NSA leak")
alice.store_secret("He doesn't see anything", "Trump leak")

alice.show_secrets()

alice.start()