#!/usr/bin/env python3

from ObliviousTransfer import One_out_of_Two

bob = One_out_of_Two()

bob.verbose = True

descriptions = bob.askDescriptions()

for d in range(len(descriptions)):
    print(d, descriptions[d])

choice = -1
while choice < 0 or choice > len(descriptions):
    try:
        choice = int(input("What secret do you want? "))
    except ValueError:
        pass
    
secret = bob.start(choice=choice)
print("\nSecret:", secret)