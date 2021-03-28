#this file contains functions specifically for the how stocks move after being the top gainer/loser of the day
#how does a stock price change the following day of being the biggest gainer or loser?


import otherfxns as o

algo = 'dayAfter' #name of the algo

def init(configFile):
  global posList,c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]


def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}")
  symbs = getUnsortedList()
  if(verbose): print(f"finding stocks for {algo}")
  goodBuys = [s for s in symbs if goodBuy(s)]
  if(verbose): print(f"{len(goodBuys)} found for {algo}")
  return goodBuys
 

#determine whether the queries symb is a good one to buy or not
def goodBuy(symb, verbose=False):
  #TODO: see how a stock's price changes after being on the gainer or loser list
  
  return False
  


#get a list of stocks to be sifted through
def getUnsortedList(verbose=False):
  symbList = {}
  while True:
    try:
      r = o.json.loads(o.request("https://api.nasdaq.com/api/marketmovers",headers={'user-agent','-'},timeout=5))['data']['STOCKS']
    except Exception:
      print("Error encoutered getting market movers. Trying again...")
      o.time.sleep(3)
  
  symbList['gainers'] = r['mostAdvanced']
  symbList['losers'] = r['mostDeclined']
  
  return symbList

#return whether symb is a good sell or not
def goodSell(symb, verbose=False):
    
  
#TODO: this should also account for squeezing
def sellUp(symb=""):
  stockList = o.json.loads(open(posListFile,'r').read())[algo] #stocks held by this algo according to the records
  mainSellUp = float(c[algo]['sellUp'])
  startSqueeze = float(c[algo]['startSqueeze'])
  squeezeTime = float(c[algo]['squeezeTime'])

  if(symb in stockList):
    #TODO: add exit condition (see it in goodBuys)
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  stockList = o.json.loads(open(posListFile,'r').read())[algo] #stocks held by this algo according to the records
  mainSellDn = float(c[algo]['sellDn'])
  if(symb in stockList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

#get the stop loss for a symbol after its been triggered (default to the main value)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
