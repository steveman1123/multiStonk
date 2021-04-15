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
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"finding stocks for {algo}...")
  arr = goodBuys(ul) #returns dict of {symb:gooduy(t/f)}
  arr = {e:"-" for e in arr if(arr[e])} #only look at the ones that are true
  if(verbose): print(f"{len(arr)} found for {algo}.")
  
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

#determine if a stock is a good sell or not
#depreciated, replaced with goodSells
def goodSell(symb):
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

  #check if price<sellDn
  buyPrice = float(stockList[symb]['buyPrice'])
  curPrice = o.getInfo(symb)['price']
  if(buyPrice>0):
    if(curPrice/buyPrice<sellDn(symb) or curPrice/buyPrice>=sellUp(symb)):
      return True #price has moved outside of the sale price
    else:
      return False
  else:
    print(f"{symb} buy price is 0.")
    return False

#multiplex the good sell function
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
  good2sell = {s:(s in curPrices and (curPrices[(s+"|stocks").upper()]['price']/buyPrices[s]<sellDn(s) or curPrices[(s+"|stocks").upper()]['price']/buyPrices[s]>=sellUp(s))) for s in buyPrices}
  
  return good2sell

#determine whether a stock is a good buy or not
#depreciated, replaced with goodBuys
def goodBuy(symb):
  return True

#determine if stocks are good to buy or not
#returns a dict with all the elements of symbList and t/f if it's a good buy {symb:goodbuy(t/f)}
def goodBuys(symbList,verbose=False):
  [minPrice,maxPrice] = [float(c[algo]['minPrice']),float(c[algo]['maxPrice'])] #get the price range
  if(verbose): print(f"min: {minPrice}, max: {maxPrice}")
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get current prices
  #make sure that price is within our target range and that the price was actually obtained
  out = {s:((s+"|stocks").upper() in prices and minPrice<=prices[(s+"|stocks").upper()]['price']<=maxPrice) for s in symbList}
  
  return out

def sellUp(symb=""):
  return float(c[algo]['sellUp'])

def sellDn(symb=""):
  return float(c[algo]['sellDn'])

def sellUpDn():
  return float(c[algo]['sellUpDn'])

def maxPrice():
  return float(c[algo]['maxPrice'])
