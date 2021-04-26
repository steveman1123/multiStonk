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
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

#TODO: this will need to change so that goodBuys basically throws out the arg list and gets a fresh one from today's movers (rather than yesterday's movers that would be generated in the morning) - as it stands list is generated in the morning of today (containing yesterday's movers) then buying happens this afternoon (after yesterday's movers have moved), so will need to regen goodbuy list to get today's movers so they should gain tomorrow

#return a dict of good buys {symb:note}
#the note will contain the original fall % for losers
def getList(isAfternoon=False, verbose=True):
  #TODO: adjust this value based on testing
  if(isAfternoon): #must be afternoon to update (to see today's biggest movers)
    minFallPerc = float(c[algo]['minFallPerc']) #price must drop by at least this much
    
    if(verbose): print(f"getting unsorted list for {algo}...")
    symbs = getUnsortedList()
    if(verbose): print(f"finding stocks for {algo}...")
    
    #
    gb = {s['symbol']:float(s['change'][:-1])/100 for s in symbList['losers']}
    #only 
    gb = {s:gb[s] for s in gb if gb[s]<=minFallPerc}
    if(verbose): print(f"{len(goodBuys)} found for {algo}.")
    return goodBuys
  else:
    return {}

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
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  
  buyPrices = {e['buyPrice'] for e in posList}
  symbList = [e for e in symbList if e in posList] #make sure they're the ones in the posList only
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  gs = {e:(e not in prices or prices[e]['price']/prices[e]['open']>=sellUp(e) or prices[e]['price']/prices[e]['open']<sellDn(e) or prices[e]['price']/buyPrices[e]>=sellUp(e) or prices[e]['price']/buyPrices[e]<sellDn(e)) for e in symbList} #return true if the price has reached a sellUp/dn point or it's not in the prices list
  
  return gs  

#get a list of stocks to be sifted through (also contains last price, and change)
def getUnsortedList(verbose=False):
  symbList = {}
  while True:
    try:
      r = o.json.loads(o.request("https://api.nasdaq.com/api/marketmovers",headers={'user-agent','-'},timeout=5).text)['data']['STOCKS']
    except Exception:
      print("Error encoutered getting market movers. Trying again...")
      o.time.sleep(3)
  
  symbList['gainers'] = r['mostAdvanced']['table']['rows']
  symbList['losers'] = r['mostDeclined']['table']['rows']
  
  return symbList
    
  
#TODO: add comments
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

  if(symb in posList):
    bouncePerc = float(c[algo]['bouncePerc']) #get the amount of rebound to look for
    lossPerc = float(posList[symb]['note']) #get the previous day's loss %
    return 1+(bouncePerc*lossPerc)
  else:
    return float(c[algo]['sellUp'])


def sellDn(symb=""):
  return float(c[algo]['sellDn'])


#get the stop loss for a symbol after its been triggered (default to the main value)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
