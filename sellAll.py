#close all positions

import sys

if(len(sys.argv)>1):
  keyfile = sys.argv[-1]
else:
  print("please supply the api key file as an argument")
  exit()

import alpacafxns as a


isPaper = True


a.init(keyfile,isPaper)

print("key file:",keyfile)
print("is paper:",isPaper)
print("")
p=a.getPos()

print(f"{len(p)} positions held")

a.closeAll(isManual=True)
