#this algo only looks at the stocks in the biopharmcatalyst.com table and makes a trading decision based on the data in it

import otherfxns as o

algo = 'fda3'

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
  j = getUnsortedList() #this should contain the entire json data, not just the list of symbols
  
  
  return []


def goodBuy(symb):
  return False
  

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

  try: #isolate the data
    arr = r.split('tabledata="')[1].split('"></screener>')[0] #contains the 150 entries in the free version of the table
    arr = o.json.loads(arr.replace("&quot;",'"'))
  except Exception:
    print(f"Bad data from biopharmcatalyst.com from {algo}")
    arr = []
  
  return arr



#TODO: this should also account for squeezing
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
