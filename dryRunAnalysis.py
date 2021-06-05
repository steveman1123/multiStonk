#this file is meant to gather a bunch of data about the stocks above a certain gain threshold (depending on the algo) and make it easy to analyze it all

import otherfxns as o
import sys,json,time,os
import datetime as dt

#where the json files are stored
listDir = "../stockStuff/dryRunLists/"

if(len(sys.argv)>2): #if there's an argument present
  if(len(sys.argv)<4):
    algo = sys.argv[1].lower()
    minGain = float(sys.argv[2])
  else:
    raise ValueError("Too many arguments. Please specify only one algo to test and the gain threshold")
else: #no argument present
  raise ValueError("Not enough arguments present. Please specify the algo to test and the gain threshold. Available algos are in "+listDir)
  

#get the stocks from the list
posList = json.loads(open(listDir+algo+".json",'r').read())

#isolate the ones that have gained enough
posList = {e:posList[e] for e in posList if posList[e]['high']>=minGain}


'''
data to get:
earning info (most recent, and past year)
historical prices
market cap
earnings surprise
blog post/headline sentiment
rsi levels
basically anything/everything we can get from ndaq
'''

