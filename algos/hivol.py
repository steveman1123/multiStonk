#this file contains functions specifically for the high volume breakout algo
#what changes when a stock has a high volume breakout? Can we see when that will happen? (also check earnings report)

import otherfxns as o

algo = 'hivol' #name of the algo
#stocks held by this algo according to the records
lock = o.threading.Lock()
lock.acquire()
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]
lock.release()

def getList(verbose=True):
  #perform checks to see which one ones will gain
  
  
  return goodBuys #return dict of symb:note
  


#TODO: this should also account for squeezing
def sellUp(symb=""):
  mainSellUp = float(o.c[algo]['sellUp'])
  if(symb in stockList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  mainSellDn = float(o.c[algo]['sellDn'])
  if(symb in stockList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(o.c[algo]['sellUpDn'])


#get a list of stocks to be sifted through
def getUnsortedList():
  return []