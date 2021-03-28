#this file contains functions specifically for the reddit algo
#how do stocks move after being discussed on reddit (in wallstreetbets, etc)?

# https://www.reddit.com/dev/api
# https://github.com/reddit-archive/reddit/wiki/API

import otherfxns as o

algo = 'reddit' #name of the algo
#stocks held by this algo according to the records
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]


def getList():
  #perform checks to see which one ones will gain
  
  return goodBuys
  

#get a list of stocks to be sifted through
#type can be spo, status can be priced|upcoming|filled|withdrawn
def getUnsortedList(status="all", type=""):
  while True:
    try:
      r = o.requests("reddit API for various market subs",timeout=5)
      break
    except Exception:
      print("Error getting unsorted list for reddit algo. Trying again...")
      o.time.sleep(3)
      pass
  
  return []


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
