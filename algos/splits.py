#this file contains functions specifically for the splits algo
#what changes when a stock splits?

import otherfxns as o

algo = 'splits' #name of the algo
#stocks held by this algo according to the records
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]


def getList(verbose=True):
  #perform checks to see which one ones will gain
  
  
  return goodBuys
  

#get a list of stocks to be sifted through
def getUnsortedList():
  while True: #get page of upcoming stock splits
    try:
      r = o.json.loads(o.requests.get("https://api.nasdaq.com/api/calendar/splits", headers={"user-agent":"-"}, timeout=5).text)['data']['rows']
      break
    except Exception:
      print("No connection, or other error encountered in reverseSplitters. trying again...")
      time.sleep(3)
      continue
  return r

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
