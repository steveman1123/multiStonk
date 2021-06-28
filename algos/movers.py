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
#the note contains the overall change %
def getList(isAfternoon=False, verbose=True):
  #TODO: adjust this value based on testing
  ul = getUnsortedList()
  out = {}
  for e in ul:
    for s in ul[e]:
      if(float(c[algo]['minPrice'])<=float(s['lastSalePrice'])<=float(c[algo]['maxPrice'])):
        out[s['symbol']] = s['change']
  return out
  
  
  
  
#determine whether the queries symb is a good one to buy or not
#this function is depreciated, replaced with goodBuys
def goodBuy(symb, verbose=False):
  #TODO: see how a stock's price changes after being on the gainer or loser list
  #may want to look at history
  #need to test this one over time like what we did with the original fda one
  
  return False
  
#return whether symb is a good sell or not
#this function is depreciated, replaced with goodSells
def goodSell(symb, verbose=False):
  #in terms of losers - theoritcally if the loss is significant in ne day, then the next day it should bounce back a bit (dead cat)
  #look for the significant drop (in goodbuy), then look for some amount of rebound from that drop
  
  inf = o.getInfo(symb,['price','open']) #get the current and open prices

  return inf['price']/inf['open']>=bouncePerc*note #return true if the price has bounced back some % of the fall

#multiplex the goodBuy fxn (symbList should be the output of getUnsortedList)
def goodBuys(symbList):
  
  minFallPerc = float(c[algo]['minFallPerc']) #price must drop by at least this much
  #
  gb = {s:(abs(float(s['change'][:-1])/100)>=minFallPerc) for s in symbList['losers']}
  return gb

#where symblist is a list of stocks and the function returns the same stocklist as a dict of {symb:goodsell(t/f)}
def goodSells(symbList):
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
  gs = {s:(s not in prices or
           prices[s]['price']/prices[s]['open']>=sellUp(s) or
           prices[s]['price']/prices[s]['open']<sellDn(s) or
           prices[(s)]['price']/buyPrices[s]<sellDn(s) or
           prices[(s)]['price']/buyPrices[s]>=sellUp(s)
          ) for s in symbList}
  
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
