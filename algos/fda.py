#this file contains functions specifically for the FDA drug approval algo
#we can see which companies are slated for an FDA drug approval. They almost always gain

import ndaqfxns as n
import os,json,threading, configparser

algo = os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

#TODO: how to handle large drops that are either potentially oversold, or valid such as what happened here (price dropped from $25 to $15 after this news):
# https://finance.yahon.com/news/cara-therapeutics-announces-topline-results-110000707.html
# ^ check how insider trading is, and upcoming important dates (like announcements of phase results, etc)
# if it still falls significantly despite those, then wait at least a week and then make a decision based on the articles being posted
#TODO: should check history to make sure that the price isn't consistently decreasing

def init(configFile):
  global posList,c
  #set the multi config file
  c = configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = threading.Lock()
  lock.acquire()
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

#get list of stocks pending FDA approvals
#eturn dict of format {"symb":"-"} (since there's no important info otherwise to report (as of right now), the values can be empty)
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
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
      r = n.requests.get("https://www.drugs.com/new-drug-applications.html", timeout=5).text
      break
    except Exception:
      print(f"No connection, or other error encountered in getUnsortedList for {algo}. trying again...")
      n.time.sleep(3)
      continue
  
  try:
    if(verbose): print("Getting company names")
    arr = r.split("Company:</b>") #go down to stock list
    arr = [e.split("<br>")[0].strip() for e in arr][1::] #get list of companies
    if(verbose): print(arr) #company names
    if(verbose): print("remove dupes, get company symbols, and remove blanks")
    arr = list(set(arr)) #remove duplicates
    arr = [n.getSymb(e) for e in arr] #get the symbols and exchanges of the companies
    arr = [e for e in arr if e is not None] #remove empty ones
    if(verbose): print(arr) #print symbs
    
  except Exception:
    print(f"Bad data from drugs.com from {algo}")
    arr = []

  if(verbose): print("ensure prices are within range")
  #get price range
  minPrice, maxPrice = float(c[algo]['minPrice']), float(c[algo]['maxPrice'])
  if(verbose): print("minPrice",minPrice,"maxPrice",maxPrice)
  #ensure tradable and prices are within range
  prices = n.getPrices([e+"|stocks" for e in arr])
  if(verbose): print(prices)
  #ensure we're within the price range
  arr = [e.split("|")[0] for e in prices if minPrice<prices[e]['price']<maxPrice]

  if(verbose): print("ensure no dupes again")
  arr = list(set(arr))
  
  return arr

#multiplex the good sell function to return dict of {symb:t/f}
def goodSells(symbList,verbose=False):
  lock = threading.Lock()
  lock.acquire()
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  
  #make sure they're the ones in the posList only
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
            f"open: {round(daychng,2)}",
            f"buy: {round(buychng,2)}",
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

#determine whether a stock is a good buy or not
#depreciated, replaced with goodBuys
def goodBuy(symb):
  return True

#determine if stocks are good to buy or not
#returns a dict with all the elements of symbList and t/f if it's a good buy {symb:goodbuy(t/f)}
def goodBuys(symbList,verbose=False):
  [minPrice,maxPrice] = [float(c[algo]['minPrice']),float(c[algo]['maxPrice'])] #get the price range
  if(verbose): print(f"min: {minPrice}, max: {maxPrice}")
  prices = n.getPrices([e+"|stocks" for e in symbList]) #get current prices
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
