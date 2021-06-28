#this file contains functions specifically for the FDA drug approval algo
#we can see which companies are slated for an FDA drug approval. They almost always gain

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

#TODO: how to handle large drops that are either potentially oversold, or valid such as what happened here (price dropped from $25 to $15 after this news):
# https://finance.yahoo.com/news/cara-therapeutics-announces-topline-results-110000707.html
# ^ check how insider trading is, and upcoming important dates (like announcements of phase results, etc)
# if it still falls significantly despite those, then wait at least a week and then make a decision based on the articles being posted

def init(configFile):
  global posList,c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
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

#get the unsorted list of stocks to be narrowed down later - format of [list,of,stocks]
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

#multiplex the good sell function to return dict of {symb:t/f}
def goodSells(symbList,verbose=False):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  symbList = [e.upper() for e in symbList if e.upper() in posList] #make sure they're the ones in the posList only
  buyPrices = {e:float(posList[e]['buyPrice']) for e in symbList} #get the prices each stock was bought at
  if(verbose): print(f"stocks in the buyPrices: {list(buyPrices)}")
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  if(verbose): print(f"stocks in prices: {list(prices)}")
  #check that it has exceeded the stopLoss or takeProfit points
  gs = {s:(s not in prices or
           prices[s]['price']/prices[s]['open']>=sellUp(s) or
           prices[s]['price']/prices[s]['open']<sellDn(s) or
           prices[(s)]['price']/buyPrices[s]<sellDn(s) or
           prices[(s)]['price']/buyPrices[s]>=sellUp(s)
          ) for s in symbList}
  
  return gs

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
