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
  
  
  
  
  
  return gb #return dict of symb:note

#return whether stocks are good purchases or not
def goodBuys(symbList):
  arr = [(e+"|stocks").upper() for e in list(set(symbList))] #remove duplicates and append the |stocks label
  prices = o.getPrices(arr) #get the current prices
  
  #narow down to stocks only within our price range
  goodBuys = [e.split("|")[0] for e in arr if(e in prices and float(c[algo]['minPrice'])<prices[e]['price']<float(c[algo]['maxPrice']))]
  #probably should do more logic after this
  
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
  
  outs = {s:(s in goodBuys) for s in symbList} #return dict of symb:goodBuy
  
  return outs
  
#determine if stocks are good to sell or not
def goodSells(symbList):
  print(f"{algo} incomplete")
  return {s:False for s in symbList}

#return whether symb is a good sell or not
def goodSell(symb):
  print(f"{algo} incomplete")
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
