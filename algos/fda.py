#this file contains functions specifically for the FDA drug approval algo
#we can see which companies are slated for an FDA drug approval. They almost always gain

import otherfxns as o

algo = 'fda' #name of the algo


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

#get list of stocks pending FDA approvals
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}")
  ul = getUnsortedList()
  if(verbose): print("Checking company wellness for {algo}")
  arr = [e for e in ul if goodBuy(e)]
  if(verbose): print(f"{len(arr)} found for fda.")
  
  return arr

def getUnsortedList(verbose=False):
  if(verbose): print(f"{algo} getting stocks from drugs.com")
  while True: #get pages of pending stocks
    try:
      r = o.requests.get("https://www.drugs.com/new-drug-applications.html", timeout=5).text
      break
    except Exception:
      print("No connection, or other error encountered in getDrugList. trying again...")
      o.time.sleep(3)
      continue
  try:
    arr = r.split("Company:</b>") #go down to stock list
    arr = [e.split("<br>")[0].strip() for e in arr][1::] #get list of companies
    arr = list(set(arr)) #remove duplicates
    arr = [o.getSymb(e,maxTries=1) for e in arr] #get the symbols and exchanges of the companies
    prices = o.getPrices([e[0] for e in arr if e[1]=="NAS"])
    arr = [e[0] for e in arr if(e[1]=="NAS" and float(c['fda']['minPrice'])<prices[e]['price']<float(c['fda']['maxPrice']))] #get the nasdaq only ones
  except Exception:
    print("Bad data from drugs.com")
    arr = []
  
  '''
  if(verbose): print(f"{algo} getting stocks from biopharmcatalyst.com")
    while True: #get pages of pending stocks
    try:
      r1 = o.requests.get("https://www.biopharmcatalyst.com/calendars/fda-calendar",timeout=5).text
      break
    except Exception:
      print("No connection, or other error encountered in getDrugList. trying again...")
      o.time.sleep(3)
      continue
  try:
    #TODO: pare down list based on some DD of the financials of the companies. Research what to look for
    arr1 = r1.split("var tickers = [")[1].split("];")[0].replace("'","").replace(" ","").split(",") #get stock list
    arr1 = list(set(arr1)) #remove duplicates
    prices = o.getPrices(arr1)
    arr1 = [e for e in arr1 if(e in prices and float(c['fda']['minPrice'])<prices[e]['price']<float(c['fda']['maxPrice']))] #remove blanks and ensure that it's listed in ndaq (o.getPrice will return 0 if it throws an error (ie. is not listed and won't show up)) and within our price range
  except Exception:
    print("Bad data from biopharmcatalyst.com")
    arr1 = []
  '''
  arr = list(set(arr))
  # arr = list(set(arr+arr1)) #combine lists and remove duplicates  
  


def goodSell(symb):
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

  #check if price<sellDn
  buyPrice = float(stockList[symb]['buyPrice'])
  curPrice = o.getPrice(symb)
  if(curPrice/buyPrice<sellDn(symb)):
    return True
  elif(curPrice/buyPrice>=sellUp(symb)):
    return True
  else:
    return False


def goodSells(symbList):
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

  #get the prices each stock was bought at
  buyPrices = {s:float(stockList[s]['buyPrice']) for s in symbList if(s in stockList)}
  #get the stock's current prices
  curPrices = o.getPrices(symbList)
  #check that it has exceeded the stopLoss or takeProfit points
  good2sell = {s:(curPrices[s]/buyPrices[s]<sellDn(s) or curPrice/buyPrice>=sellUp(s)) for s in buyPrice}
  
  return good2sell

#TODO: make a goodBuys function too
def goodBuy(symb):
  '''
  check mktcap
  info
  
  check revenue, profit, margin trends for past 2 years.
  financials
  
  find competitors
  https://api.nasdaq.com/api/news/topic/articlebysymbol?q=gnus|stocks&offset=0&limit=7 (not technically competitors, but some general sentiment)
  
  compare p/e ratios between the target company and its competitors
  peg-ratio, analyst research
  
  management (founders, or new management? How long have they been in office?)
  insider activity
  
  review balance sheet (good cash balances and looking at amount of debt based on company's business model, industry, and age (r&d))
  financials
  
  look at how many insititutions are holding/increasing/decreasing amt, also what % they own of the company
  institution-holding
  
  historical prices
  historical
  
  total calls/stock: 7
  '''
  

#TODO: this should also account for squeezing
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  mainSellUp = float(c[algo]['sellUp'])
  if(symb in stockList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  mainSellDn = float(c[algo]['sellDn'])
  if(symb in stockList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(c[algo]['sellUpDn'])

def maxPrice():
  return float(c[algo]['maxPrice'])
