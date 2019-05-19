#!/usr/bin/env python3

from ObliviousTransfer import One_out_of_Two

alice = One_out_of_Two(client=False)

alice.verbose = True

alice.store_secret("A", "Some description")
alice.store_secret("B", "Another description")

alice.show_secrets()

alice.start()