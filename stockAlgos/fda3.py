#this algo only looks at the stocks in the biopharmcatalyst.com table and makes a trading decision based on the data in it

import otherfxns as o


algo = 'fda3'

def init(configFile):
  global c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)


def getList(verbose=True):
  j = getUnsortedList() #this should contain the entire json data, not just the list of symbols

  #min and max prices
  [minPrice, maxPrice] = [float(c[algo]['minPrice']),float(c[algo]['maxPrice'])]
  
  smaDays = int(c[algo]['smaDays']) #number of trading days to perform a simple moving average over
  twelveMgain = float(c[algo]['twelveMgain']) #stock must gain this much in the last 12 months
  sixMgain = float(c[algo]['sixMgain']) #stock must gain this much in the last 12 months  

  if(verbose): print(len(j))
  #make sure that the earnings are present (that is: it has history on the market)
  tradable = [e for e in j if e['cashflow']['earnings'] is not None]
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
  gainers = [e['companies']['ticker'] for e in upcoming]
  out = []
  for s in gainers:
    hist = o.getHistory(s) #get history
    dates = [o.dt.datetime.strptime(e[0],"%m/%d/%Y") for e in hist] #convert dates to dt format
    prices = [float(e[1]) for e in hist] #isolate the closing prices
    normPrices = [p/prices[-1] for p in prices] #normalize prices based on the first value
    if(o.mean(normPrices[0:smaDays])>twelveMgain*o.mean(normPrices[-(1+smaDays):-1]) and o.mean(normPrices[0:smaDays])>sixMgain*o.mean(normPrices[int((len(hist)-smaDays)/2):int((len(hist)+smaDays)/2)])): #make sure that it's increased in the last year and the last 6 months
      out.append(s)
  
  if(verbose): print(len(out))
  return out


#return whether symb is a good sell or not
def goodSell(symb):
  
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  
  if(symb in posList):
    #return true if outside of sellUp or sellDn
    buyPrice = posList[symb]['buyPrice']
    inf = o.getInfo(symb,['price','open'])
    
    '''
    TODO
    getlist should always return dict rather than list - of format {symb:note}
  
    on a buy and in syncposlist, note should be updated to what's in getlist
    '''
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


#TODO: this should also account for squeezing
#TODO: This should change depending on if it's before or after the catalyst date - sellDn and sellUp should increase (eg from 0.7-1.2 to 0.85-1.5)
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

  preSellUp = float(c[algo]['preSellUp'])
  postSellUp = float(c[algo]['postSellUp'])
  if(symb in posList):
    if(str(o.dt.date.today())>posList[symb]['note']):
      sellUp = postSellUp
    else:
      sellUp = preSellUp
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

  mainSellDn = float(c[algo]['sellDn'])
  if(symb in posList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():

  return float(c[algo]['sellUpDn'])
