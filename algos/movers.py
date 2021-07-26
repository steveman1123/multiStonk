#this file contains functions specifically for the how stocks move after being the top gainer/loser of the day
#how does a stock price change the following day of being the biggest gainer or loser?


import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

def init(configFile):
  global posList,c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())
  if(algo in posList):
    posList = posList[algo]
  else:
    posList = {}
  lock.release()

#TODO: this will need to change so that goodBuys basically throws out the arg list and gets a fresh one from today's movers (rather than yesterday's movers that would be generated in the morning) - as it stands list is generated in the morning of today (containing yesterday's movers) then buying happens this afternoon (after yesterday's movers have moved), so will need to regen goodbuy list to get today's movers so they should gain tomorrow
#TODO: see also momentum trading: https://www.investopedia.com/trading/introduction-to-momentum-trading/
# ^ https://api.nasdaq.com/api/analyst/{symb}/estimate-momentum

#return a dict of good buys {symb:note}
#the note contains the % seen on the date
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"finding stocks for {algo}...")
  arr = goodBuys(ul) #returns dict of {symb:gooduy(t/f)}
  arr = {e:ul[e] for e in arr if(arr[e])} #only look at the ones that are true
  if(verbose): print(f"{len(arr)} found for {algo}.")
  
  return arr
  
  
  
#multiplex the goodBuy fxn (symbList should be the output of getUnsortedList)
def goodBuys(symbList,verbose=False):
  [minPrice, maxPrice] = [float(c[algo]['minPrice']),float(c[algo]['maxPrice'])]
  [maxLoss, maxGain] = [float(c[algo]['maxLoss']),float(c[algo]['maxGain'])]
  if(verbose): print(f"minPrice: {minPrice}, maxPrice: {maxPrice}")
  if(verbose): print(f"maxLoss: {maxLoss}, maxGain: {maxGain}")

  prices = o.getPrices([e+"|stocks" for e in symbList]) #get current prices
  #make sure that price is within our target range and that the change amount is also within our range
  gb = {s:((s+"|stocks").upper() in prices and
            minPrice<=prices[(s+"|stocks").upper()]['price']<=maxPrice and
            maxLoss<=float(symbList[s])<=maxGain) for s in symbList}
  
  return gb

#where symblist is a list of stocks and the function returns the same stocklist as a dict of {symb:goodsell(t/f)}
def goodSells(symbList,verbose=False):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  symbList = [e.upper() for e in symbList if e.upper() in posList] #make sure they're the ones in the posList only
  buyPrices = {e:float(posList[e]['buyPrice']) for e in symbList} #get the prices each stock was bought at
  if(verbose): print(f"stocks in the buyPrices: {list(buyPrices)}")
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  if(verbose): print(f"stocks in prices: {list(prices)}")
  #check that it has exceeded the stopLoss or takeProfit points
  gs = {}
  for s in symbList:
    if(s in prices):
      if(verbose): print(f"{s}\topen: {round(prices[s]['price']/prices[s]['open'],2)}\tbuy: {round(prices[s]['price']/buyPrices[s],2)}\tsellUp: {sellUp(s)}\tsellDn: {sellDn(s)}")
      #check if price triggered up
      if(prices[s]['open']>0 and buyPrices[s]>0):
        if(prices[s]['price']/prices[s]['open']>=sellUp(s) or prices[s]['price']/buyPrices[s]>=sellUp(s)):
          gs[s] = 1
        #check if price triggered down
        elif(prices[s]['price']/prices[s]['open']<sellDn(s) or prices[s]['price']/buyPrices[s]<sellDn(s)):
          gs[s] = -1
        else: #price didn't trigger either side
          gs[s] = 0
      else: #TODO: is this correct? Should it sell if it can't find a price?
        gs[s] = 0
    else:
      gs[s] = 0
  
  return gs

#get a list of stocks to be sifted through (also contains last price, and change)
def getUnsortedList(verbose=False,maxTries=3):
  symbList = {}
  tries=0
  while tries<maxTries:
    try:
      r = o.requests.get("https://api.nasdaq.com/api/marketmovers",headers=o.HEADERS,timeout=5).text #get the data
      r = r.replace("%","").replace("+","").replace("$","") #get rid of supurfulous symbols
      r = o.json.loads(r)['data']['STOCKS'] #cconvert to json object (dict)
      symbList['gainers'] = r['MostAdvanced']['table']['rows']
      symbList['losers'] = r['MostDeclined']['table']['rows']
      if(verbose): print(f"{len(symbList['gainers'])} total gainers, {len(symbList['losers'])} total losers")
      break
    except Exception:
      print("Error encoutered getting market movers. Trying again...")
      tries+=1
      if(verbose): print(f"{tries}/{maxTries}")
      o.time.sleep(3)
  
  #return of format {gainers/losers:{symbol,name,lastprice,lastchange,lastchangepct}}
  return symbList
    
  
#TODO: add comments
def sellUp(symb=""):
  mainSellUp = float(c[algo]['sellUp'])
  if(symb in posList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp


def sellDn(symb=""):
  mainSellDn = float(c[algo]['sellDn'])
  if(symb in posList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn


#get the stop loss for a symbol after its been triggered (default to the main value)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
