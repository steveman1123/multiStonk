#this algo only looks at the stocks in the biopharmcatalyst.com table and makes a trading decision based on the data in it

import otherfxns as o


algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

def init(configFile):
  global c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)

#return a dict of symb:note} where the note is the catalyst date
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
  if(verbose): print(f"finding stocks for {algo}...")
  out = goodBuys(ul) #returns dict of {symb:gooduy(t/f)}
  if(verbose): print(f"{len(out)} found for {algo}.")
  return out

#return whether stocks are good buys or not - dict format {symb:goodBuyText} where goodBuyText is the status (will be the catalyst date if it is a good buy)
def goodBuys(symbList, verbose=False): #where symbList is the output of getUnsortedList()
  #min and max prices
  [minPrice, maxPrice] = [float(c[algo]['minPrice']),float(c[algo]['maxPrice'])]
  
  smaDays = int(c[algo]['smaDays']) #number of trading days to perform a simple moving average over
  twelveMgain = float(c[algo]['twelveMgain']) #stock must gain this much in the last 12 months
  sixMgain = float(c[algo]['sixMgain']) #stock must gain this much in the last 12 months  

  if(verbose): print(len(symbList))
  #make sure that the earnings are present (that is: it has history on the market)
  tradable = [e for e in symbList if e['cashflow']['earnings'] is not None]
  if(verbose): print(len(tradable))
  #only look at stocks in our price range
  goodPrice = [e for e in tradable if minPrice<=e['companies']['price']<=maxPrice]
  if(verbose): print(len(goodPrice))
  #make sure we're in the pdufa stage so we can see a history of gains
  pdufa = [e for e in goodPrice if 'pdufa' in e['stage']['value']]
  if(verbose): print(len(pdufa))
  #only look at upcoming ones, not any catalysts from the past (only present in the list because of delays)
  upcoming = [e for e in pdufa if o.dt.datetime.strptime(e['catalyst_date'],"%Y-%m-%d").date()>o.dt.date.today()]
  if(verbose): print(len(upcoming))
  
  #look for the ones that are gaining within the past year and past 6 months
  out = {}
  for s in upcoming:
    symb = s['companies']['ticker']
    hist = o.getHistory(symb) #get history
    dates = [o.dt.datetime.strptime(e[0],"%m/%d/%Y") for e in hist] #convert dates to dt format
    prices = [float(e[1]) for e in hist] #isolate the closing prices
    normPrices = [p/prices[-1] for p in prices] #normalize prices based on the first value
    if(len(normPrices)>smaDays and 
       o.mean(normPrices[0:smaDays])>twelveMgain*o.mean(normPrices[-(1+smaDays):-1]) and 
       o.mean(normPrices[0:smaDays])>sixMgain*o.mean(normPrices[int((len(hist)-smaDays)/2):int((len(hist)+smaDays)/2)])): #make sure that it's increased in the last year and the last 6 months
      out[symb] = s['catalyst_date']
  
  if(verbose): print(len(out))
  
  return out


#return whether stocks are good sells or not
def goodSells(symbList,verbose=False): #where symbList is a list of symbols
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  
  symbList = [e for e in symbList if e.upper() in posList] #make sure they're the ones in the posList only
  buyPrices = {e:posList[e]['buyPrice'] for e in symbList} #get the prices each stock was bought at
  if(verbose): print(f"stocks in the buyPrices: {list(buyPrices)}")
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  if(verbose): print(f"stocks in prices: {list(prices)}")
  #should return true if it doesn't show up in the price list or the price is now out of bounds
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
      else:
        gs[s] = 0
    else:
      gs[s] = 0
  
  return gs    

#return whether symb is a good sell or not
#this function is depreciated, replaced with goodSells
def goodSell(symb):
  
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(symb in posList):
    #return true if outside of sellUp or sellDn
    buyPrice = posList[symb]['buyPrice']
    inf = o.getInfo(symb,['price','open'])
    
    if(buyPrice>0):
      out = (inf['price']/buyPrice>=sellUp(symb) or inf['price']/buyPrice<sellDn(symb)) or (inf['price']/inf['open']>=sellUp(symb) or inf['price']/inf['open']<sellDn(symb))
    else:
      out = inf['price']/inf['open']>=sellUp(symb) or inf['price']/inf['open']<sellDn(symb)
  
    return out

  else:
    print(f"{symb} not found in {algo} in posList.")
    return True

#get a list of stocks to be sifted through
def getUnsortedList(verbose=False):
  if(verbose): print(f"{algo} getting stocks from biopharmcatalyst.com")
  while True: #get pages of pending stocks
    try:
      r = o.requests.get("https://www.biopharmcatalyst.com/calendars/fda-calendar",timeout=5).text
      break
    except Exception:
      print(f"No connection, or other error encountered in getUnsortedList in {algo}. trying again...")
      o.time.sleep(3)
      continue

  try: #isolate the data
    arr = r.split('tabledata="')[1].split('"></screener>')[0] #contains the 150 entries in the free version of the table
    arr = o.json.loads(arr.replace("&quot;",'"'))
  except Exception:
    print(f"Bad data from biopharmcatalyst.com from {algo}")
    arr = []

  return arr


#TODO: should possibly have a global posList value that's updated once a day? That way we're not reading from the file constantly (that would speed things up (there is no effective read limit like there is with a write limit))
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

  preSellUp = float(c[algo]['preSellUp']) #sell % before the catalyst date
  postSellUp = float(c[algo]['postSellUp']) #sell % after the catalyst date
  if(symb in posList and str(o.dt.date.today())>posList[symb]['note']):
    return postSellUp
  else:
    return preSellUp

def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

  preSellDn = float(c[algo]['preSellDn']) #sell % before the catalyst date
  postSellDn = float(c[algo]['postSellDn']) #sell % after the catalyst date
  if(symb in posList and str(o.dt.date.today())>posList[symb]['note']):
     return postSellDn
  else:
    return preSellDn

def sellUpDn():

  return float(c[algo]['sellUpDn'])
