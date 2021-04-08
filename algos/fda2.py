#this algo only looks at the stocks in the biopharmcatalyst.com big list of symbols and runs some due diligence on them to see if they're a good buy

import otherfxns as o

algo = 'fda2'

def init(configFile):
  global c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

def getList(verbose=True):
  
  
  
  
  
  return []


def goodBuys(symbList):
  arr = [e+"|stocks" for e in list(set(arr))] #remove duplicates and append the |stocks label
  prices = o.getPrices(arr)
  arr = [e for e in arr if(e in prices and float(c['fda']['minPrice'])<prices[e]['price']<float(c['fda']['maxPrice']))] #remove blanks and ensure that it's listed in ndaq (o.getPrice will return 0 if it throws an error (ie. is not listed and won't show up)) and within our price range
  return {'symb':False}
  

#return whether symb is a good sell or not
def goodSell(symb):
  return False

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
  try:
    #TODO: pare down list based on some DD of the financials of the companies. Research what to look for
    arr = r.split("var tickers = [")[1].split("];")[0].replace("'","").replace(" ","").split(",") #get stock list - contains the 800 or so tickers from the premium version
  except Exception:
    print(f"Bad data from biopharmcatalyst.com from {algo}")
    arr = []
  
  return []



#TODO: this should also account for squeezing
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  
  mainSellUp = float(c[algo]['sellUp'])
  if(symb in posList):
    #TODO: add exit condition (see it in getList)
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
