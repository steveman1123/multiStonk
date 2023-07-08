#this algo only looks at the stocks in the bpiq.com table and makes a trading decision based on the data in it

import ndaqfxns as n
import os,time,json,threading,configparser,requests
import datetime as dt

algo = os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

def init(configFile,verbose=False):
  global c,posList

  if(verbose): print(f"reading config file {configFile}")
  #set the multi config file
  c = configparser.ConfigParser()
  c.read(configFile)
  
  #get the stocks held by this algo according to the records
  posListFile = c['file locations']['posList']
  if(verbose): print(f"reading posList file {posListFile}")
  lock = threading.Lock()
  lock.acquire()
  #read the whole file
  with open(posListFile,'r') as f:
    algoPos = json.loads(f.read())['algos']
    f.close()
  lock.release()
  if(algo in algoPos):
    if(verbose): print(f"{algo} is in posListFile with {len(algoPos[algo])} stocks")
    posList = algoPos[algo]
  else:
    if(verbose): print(f"{algo} not found in posList, init to empty")
    posList = {}

#return a dict of symb:note} where the note is the catalyst date
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
  if(verbose): print(f"finding stocks for {algo}...")
  out = goodBuys(ul) #returns dict of {symb:goodbuy(t/f)}
  if(verbose): print(f"{len(out)} found for {algo}.")
  return out

#THIS FUNCTION IS DEPRECIATED - it was for use on data from biopharmcatalyst. Keeping just in case for reference
#return whether stocks are good buys or not
#return dict format {symb:goodBuyText} where goodBuyText is the status (will be the catalyst date if it is a good buy)
#symbList = output of getUnsortedList()
def goodBuys_old(symbList, verbose=False):
  #min and max prices
  minPrice, maxPrice = float(c[algo]['minPrice']), float(c[algo]['maxPrice'])
  
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
  upcoming = [e for e in pdufa if dt.datetime.strptime(e['catalyst_date'],"%Y-%m-%d").date()>dt.date.today()]
  if(verbose): print(len(upcoming))
  
  #look for the ones that are gaining within the past year and past 6 months
  out = {}
  for s in upcoming:
    symb = s['companies']['ticker']
    hist = n.getHistory(symb) #get history
    dates = [dt.datetime.strptime(e[0],"%m/%d/%Y") for e in hist] #convert dates to dt format
    prices = [float(e[1]) for e in hist] #isolate the closing prices
    normPrices = [p/prices[-1] for p in prices] #normalize prices based on the first value
    if(len(normPrices)>smaDays and 
       n.mean(normPrices[0:smaDays])>twelveMgain*n.mean(normPrices[-(1+smaDays):-1]) and 
       n.mean(normPrices[0:smaDays])>sixMgain*n.mean(normPrices[int((len(hist)-smaDays)/2):int((len(hist)+smaDays)/2)])): #make sure that it's increased in the last year and the last 6 months
      out[symb] = s['catalyst_date']
  
  if(verbose): print(len(out))
  
  return out


#return whether stocks are good buys or not
#return dict format {symb:goodBuyText} where goodBuyText is the status (will be the catalyst date if it is a good buy)
#symbList = output of getUnsortedList()
def goodBuys(symbList,verbose=False):
  minPrice, maxPrice = float(c[algo]['minPrice']), float(c[algo]['maxPrice'])
  out = {e['ticker']:e['catalyst_date'] for e in symbList if minPrice<=float(e['company']['last_price'])<=maxPrice and e['is_suspected_mover']}
  return out

#return whether stocks are good sells or not
#symbList = list of position objects from alpaca (output of getPos())
def goodSells(symbList,verbose=False):

  #read the currently held positions
  lock = threading.Lock()
  lock.acquire()
  #currently held positions of this algo
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  
  #only get the objects of the symbs that are held in this algo
  #symblist is now alpaca position objects for stocks held in this algo
  symbList = [e for e in symbList if e['symbol'] in posList]
  
  #check that it has exceeded the stopLoss or takeProfit points
  gs = {}
  for s in symbList:
    su = sellUp(s['symbol'])
    sd = sellDn(s['symbol'])
  
    daychng = float(s['change_today'])+1 #current price/last close price
    buychng = float(s['unrealized_plpc'])+1 #current price/buy price
    
    if(verbose): 
      print(f"{s['symbol']}",
            f"open: {round(daychng,2)}", #change since open
            f"buy: {round(buychng,2)}", #change since buy
            f"sellUp: {su}",
            f"sellDn: {sd}")
    
    #check if price triggered up
    if(daychng>=su or buychng>=su):
      gs[s['symbol']] = 1
    #check if price triggered down
    elif(daychng<sd or buychng<sd):
      gs[s['symbol']] = -1
    else: #price didn't trigger either side
      gs[s['symbol']] = 0
      
  #display stocks that have an error
  for e in [e for e in symbList if e['symbol'] not in gs]:
    print(f"{e['symbol']} not tradable in {algo}")
  
  return gs


#return whether symb is a good sell or not
#this function is depreciated, replaced with goodSells
def goodSell(symb):
  
  lock = threading.Lock()
  lock.acquire()
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(symb in posList):
    #return true if outside of sellUp or sellDn
    buyPrice = posList[symb]['buyPrice']
    inf = n.getInfo(symb,['price','open'])
    
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
  if(verbose): print(f"{algo} getting stocks from bpiq.com")
  while True: #get pages of pending stocks
    try:
      params = {"catalyst_date_max":dt.date.today()+dt.timedelta(days=28), #look for a catalyst between now and the specified date - days specified is arbitrary
                "limit":100, #somewhat arbitrary, larger will load slower, but probably won't be >75 anyways
                }
      r = requests.get("https://api.bpiq.com/api/v1/drugs/screener",params=params,timeout=5).json()['results']
      break
    except Exception:
      print(f"No connection, or other error encountered in getUnsortedList in {algo}. trying again...")
      time.sleep(3)
      continue

  if(verbose): print(f"found {len(r)} companies")

  return r


#TODO: should possibly have a global posList value that's updated once a day? That way we're not reading from the file constantly (that would speed things up (there is no effective read limit like there is with a write limit))
def sellUp(symb=""):
  lock = threading.Lock()
  lock.acquire()
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

  preSellUp = float(c[algo]['preSellUp']) #sell % before the catalyst date
  postSellUp = float(c[algo]['postSellUp']) #sell % after the catalyst date
  if(symb in posList and str(dt.date.today())>posList[symb]['note']):
    return postSellUp
  else:
    return preSellUp

def sellDn(symb=""):
  lock = threading.Lock()
  lock.acquire()
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

  preSellDn = float(c[algo]['preSellDn']) #sell % before the catalyst date
  postSellDn = float(c[algo]['postSellDn']) #sell % after the catalyst date
  if(symb in posList and str(dt.date.today())>posList[symb]['note']):
     return postSellDn
  else:
    return preSellDn

def sellUpDn():

  return float(c[algo]['sellUpDn'])
