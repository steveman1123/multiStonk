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
  if(verbose): print(f"Checking company wellness for {algo}")
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
      print(f"No connection, or other error encountered in getUnsortedList for {algo}. trying again...")
      o.time.sleep(3)
      continue
  try:
    arr = r.split("Company:</b>") #go down to stock list
    arr = [e.split("<br>")[0].strip() for e in arr][1::] #get list of companies
    arr = list(set(arr)) #remove duplicates
    arr = [o.getSymb(e,maxTries=1) for e in arr] #get the symbols and exchanges of the companies
    prices = o.getPrices([e[0]+"|stocks" for e in arr if e[1]=="NAS"]) #get only the nasdaq ones
    arr = [e.split("|")[0] for e in prices if(float(c['fda']['minPrice'])<prices[e]['price']<float(c['fda']['maxPrice']))] #ensure we're within the price range
  except Exception:
    print(f"Bad data from drugs.com from {algo}")
    arr = []
  
  
  arr = list(set(arr))
  # arr = list(set(arr+arr1)) #combine lists and remove duplicates  
  return arr


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
def goodBuy(symb, maxTries=3):
  '''
  #get basic company info (for mktcap)
  tries=0
  while tries<maxTries:
    try:
      inf=o.requests.get(f"https://api.nasdaq.com/api/quote/{symb}/info?assetclass=stocks",headers={'user-agent':'-'},timeout=5)
      break
    except Exception:
      print(f"Error getting info in goodBuy for {symb}")
      o.time.sleep(3)
      tries+=1
      continue

  #get company financials (for revenue, profit, etc)
  tries=0
  while tries<maxTries:
    try:
      fin=o.requests.get(f"https://api.nasdaq.com/api/company/{symb}/financials?frequency=1",headers={'user-agent':'-'},timeout=5)
      break
    except Exception:
      print(f"Error getting financials in goodBuy for {symb}")
      o.time.sleep(3)
      tries+=1
      continue

  #get company headlines (for comparison to other companies and industry)
  tries=0
  while tries<maxTries:
    try:
      headlines=o.requests.get(f"https://api.nasdaq.com/api/news/topic/articlebysymbol?q={symb}|stocks&offset=0&limit=7",headers={'user-agent':'-'},timeout=5)
      break
    except Exception:
      print(f"Error getting headlines in goodBuy for {symb}")
      o.time.sleep(3)
      tries+=1
      continue


  #get the P/E ratio
  tries=0
  while tries<maxTries:
    try:
      peg=o.requests.get(f"https://api.nasdaq.com/api/analyst/{symb}/peg-ratio",headers={'user-agent':'-'},timeout=5)
      break
    except Exception:
      print(f"Error getting peg ratio in goodBuy for {symb}")
      o.time.sleep(3)
      tries+=1
      continue

  #get analyst ratings
  tries=0
  while tries<maxTries:
    try:
      ratings=o.requests.get(f"https://api.nasdaq.com/api/analyst/{symb}/ratings",headers={'user-agent':'-'},timeout=5)
      break
    except Exception:
      print(f"Error getting ratings in goodBuy for {symb}")
      o.time.sleep(3)
      tries+=1
      continue

  #get institutional holdings
  tries=0
  while tries<maxTries:
    try:
      insthold=o.requests.get(f"https://api.nasdaq.com/api/company/{symb}/institutional-holidings",headers={'user-agent':'-'},timeout=5)
      break
    except Exception:
      print(f"Error getting institutional holdings in goodBuy for {symb}")
      o.time.sleep(3)
      tries+=1
      continue

  #get historical price data
  hist = o.getHistory(symb, str(dt.date.today()-dt.timedelta(60)), str(dt.date.today())) #TODO: don't use a magic number for how many days to get
  '''
  
  #this analysis is going to be fairly subjective, but here's what I'm thinking:
  '''
  if # of analyst rating > 3 and consensus is buy or strong buy, then is good
  else:
    check info, make sure is nasdaq listed, price is within our target point and volume is above a certain threshold (must have some liquidity)
    if it meets those requirements:
      check headlines. Look for positive/negative sentiment. if pos then:
        check the financials, see if profit margins are generally rising, look for low (relative to industry/competition) p/e ratio
        if it meets those critera:
          see if other institutions are holding it, then
          if there is recent insider trading then follow its direction
  '''
  
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
  return True

def goodBuys(symbList, maxTries=3):
  return {'symb':False}

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
