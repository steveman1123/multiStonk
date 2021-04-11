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
  minPct = float(c[algo]['minPct']) #minimum percent that the jumps should be at
  spikeTime = int(c[algo]['spikeTime']) #min number of trading days between spikes
  
  print(len(j))
  #make sure that the earnings are present (that is: it has history on the market)
  tradable = [e for e in j if e['cashflow']['earnings'] is not None]
  print(len(tradable))
  #only look at stocks in our price range
  goodPrice = [e for e in tradable if minPrice<=e['companies']['price']<=maxPrice]
  print(len(goodPrice))
  #make sure we're in the pdufa stage
  pdufa = [e for e in goodPrice if 'pdufa' in e['stage']['value']]
  print(len(pdufa))
  #only look at upcoming ones, not any catalysts from the past (only present in the list because of delays)
  upcoming = [e for e in pdufa if o.dt.datetime.strptime(e['catalyst_date'],"%Y-%m-%d").date()>o.dt.date.today()]
  print(len(upcoming))
  #check history for recent price/volume jumps
  #TODO: how badly do we want to implement this? upcoming contains about 20 which is fairly managable
  # for e in upcoming:
    # hist = o.getHistory(e['cashflow']['ticker']) #get the last year's worth of price history
    #look for major spikes away from the moving average (at least some %)
    #the spikes should be increasing in % away from average. moving average should also be going up
    
    
  
  return [e['companies']['ticker'] for e in upcoming]


#return whether symb is a good sell or not
def goodSell(symb):
  #return true if outside of sellUp or sellDn
  
  '''
  TODO
  getlist should always return dict rather than list of format {symb:note}

  on a buy and in syncposlist, note should be updated to what's in getlist
  '''
  out = 
  
  return out


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

  mainSellUp = float(c[algo]['sellUp'])
  if(symb in posList):
    sellUp = mainSellUp #TODO: account for squeeze here
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
