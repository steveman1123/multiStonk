#this file contains functions specifically for the stocks that are listed in investopedia - these are probably updated monthly
# https://www.investopedia.com/updates/top-penny-stocks/

import ndaqfxns as n
import os,requests,json,time,re,configparser,threading
import datetime as dt

algo = os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

def init(configFile,verbose=False):
  global c,posList

  if(verbose): print(f"reading config file {configFile}")
  #set the multi config file
  c = configparser.ConfigParser()
  c.read(configFile)
  
  #get the stocks held by this algo according to the records
  posListFile = c['file locations']['posList']
  if(verbose): print(f"reading posList file {posListFile}")
  lock = threading.Lock()
  lock.acquire()
  #read the whole file
  with open(posListFile,'r') as f:
    algoPos = json.loads(f.read())['algos']
    f.close()
  lock.release()
  if(algo in algoPos):
    if(verbose): print(f"{algo} is in posListFile with {len(algoPos[algo])} stocks")
    posList = algoPos[algo]
  else:
    if(verbose): print(f"{algo} not found in posList, init to empty")
    posList = {}


#return a dict of good buys {symb:note}
#the note contains the overall change %
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
  if(verbose): print(f"finding stocks for {algo}...")
  arr = goodBuys(ul) #returns dict of {symb:gooduy(t/f)}
  arr = {e:ul[e] for e in arr if(arr[e])} #only look at the ones that are true
  if(verbose): print(f"{len(arr)} found for {algo}.")
  
  return arr

#multiplex the goodBuy fxn (symbList should be the output of getUnsortedList)
#return dict of {symb:t/f}
def goodBuys(symbList,verbose=False):
  #TODO: check prices and other info investopedia may have (plus cross reference with other sites)
  if(verbose): print(symbList)

  [minPrice,maxPrice] = [float(c[algo]['minPrice']),float(c[algo]['maxPrice'])] #get the price range
  if(verbose): print(f"min: {minPrice}, max: {maxPrice}")
  prices = n.getPrices([e+"|stocks" for e in symbList],verbose=False) #get current prices
  if(verbose): print(*prices,sep="\n")
  #make sure that price is within our target range and that the price was actually obtained
  out = {s:((s+"|stocks").upper() in prices and minPrice<=prices[(s+"|stocks").upper()]['price']<=maxPrice) for s in symbList}
  
  return out



#multiplex the good sell function to return dict of {symb:t/f}
def goodSells(symbList,verbose=False):
    #read the currently held positions
  lock = threading.Lock()
  lock.acquire()
  #currently held positions of this algo
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  
  #only get the objects of the symbs that are held in this algo
  #symblist is now alpaca position objects for stocks held in this algo
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
            f"open: {round(daychng,2)}", #change since open
            f"buy: {round(buychng,2)}", #change since buy
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



#get a list of stocks to be sifted through
#returns dict of {symb:"date, type"}
def getUnsortedList(verbose=False,maxTries=3):
  out = {}
  
  #TODO: use robreq instead of straight requests

  #specify the type and the url to get the stocks from
  stockTypes = {
    "top":"https://www.investopedia.com/updates/top-penny-stocks/",
    "t-ana":"https://www.investopedia.com/updates/penny-stocks-buy-technical-analysis/",
    "oilgas":"https://www.investopedia.com/investing/oil-gas-penny-stocks",
    "tech":"https://www.investopedia.com/investing/technology-penny-stocks"
  }


  #get the various stocks
  for stockType in stockTypes:
    tries=0
    while tries<maxTries or maxTries<0:
      try:
        r = requests.get(stockTypes[stockType],headers=n.HEADERS,timeout=5).text #get the data
        #get the date last published/updated (contained within the "mntl..." element, first word is either "updated" or "published", split by spaces, remove first word, and rejoin with spaces)
        d = " ".join(r.split('"mntl-attribution__item-date">')[1].split("<")[0].split(" ")[1:])
        # print(d)

        #convert from "Month dd, yyyy" to yyyy-mm-dd
        d = str(dt.datetime.strptime(d,"%B %d, %Y").date())
        
        #get the stock symbols
        #symbols used to be in an email header
        # s = r.split('"emailtickers" content="')[1].split('" />')[0].split(",")
        #pull symbols from tables
        s = r.split("\n")
        s = set([l.split("tvwidgetsymbol=")[1].split('"')[0] for l in s if l.startswith("<td>") and "tvwidgetsymbol=" in l])

        
        #convert to dict of format {symb:"updated-date, type"}
        symbList = {e:d+", "+stockType for e in s}

        out.update(symbList) #append to output
        break
      except Exception as e:
        print(e)
        print(f"Error encoutered getting investopedia {stockType} stocks. Trying again...")
        if(verbose): print(f"{tries}/{maxTries}")
        tries+=1
        time.sleep(3)

  #remove any symbol with a "." in it since those aren't usually valid and make sure there's no erroneous whitespace
  out = {e.strip():out[e] for e in out if "." not in e}
  return out
    
  
#determine how much the take-profit should be for change since buy or change since close
def sellUp(symb=""):
  return float(c[algo]['sellUp'])

#determine how much the stop-loss should be for change since buy or change since close
def sellDn(symb=""):
  return float(c[algo]['sellDn'])


#get the stop loss for a symbol after its been triggered (default to the main value)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
