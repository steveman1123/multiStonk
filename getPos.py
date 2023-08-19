#get the current positions and save to a file

print("starting up")
import alpacafxns as a
import json

configFile = "configs/multi.config"
c = a.n.configparser.ConfigParser()
c.read(configFile)

a.init(c['file locations']['keyFile'],int(c['account params']['isPaper']))

print("getting posList")
p = a.getPos()

print("writing file")
with open("alpaca-pos.json",'w') as f:
  f.write(json.dumps(p))
  f.close()
print("done")
