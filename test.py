# import alpacafxns as a
import json
import algos.divs as d

d.init("configs/multi.config",True)


posList = json.loads(open("posListMulti.json",'r').read())

symbList = posList['algos']['divs']


d.goodSells(symbList,True)

