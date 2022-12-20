#this file contains functions specifically for the exponential moving average algo
#how can we apply an ema to various stocks?
#https://tradingstrategyguides.com/exponential-moving-average-strategy/
#https://www.investopedia.com/terms/e/ema.asp
#also, an ema can work across multiple exchange types, not just for stocks
#this specific one will look at stocks over a period of days

import otherfxns as o
from workdays import workday as wd
from workdays import networkdays as nwd

#TODO: add verbose setting to (at the very least) getList, goodBuy, and goodSell

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name


def init(configFile):
  global posList,c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())
  if(algo in posList):
    posList = posList[algo]
  else:
    posList = {}
  lock.release()

#get list of stocks that have triggered the EMA buy conditions
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
  if(verbose): print(f"finding stocks for {algo}...")
  gb = goodBuys(ul,True) #returns dict of {symb:note}
  if(verbose): print(f"{len(gb)} found for {algo}.")
  return gb
 

#get a list of stocks to be sifted through
#TODO: should make this an otherfxns fxn with params so multiple algos can pull from the same code
def getUnsortedList(verbose=False, maxTries=3):
  symbList = list()
  url = "https://www.marketwatch.com/tools/screener/stock"
  
  params = {
    "exchange" : "nasdaq",
    "visiblecolumns" : "Symbol",
    "pricemin" : str(c[algo]['minPrice']),
    "pricemax" : str(c[algo]['maxPrice']),
    "volumemin" : str(c[algo]['minVol']),
    "partial" : "true"
  }
  
  if(verbose): print("Getting MarketWatch data...")
  skip = 0
  resultsPerPage = 25 #new screener only returns 25 per page and can't be changed (afaict)
  pageList = [None] #init to some value so that its not empty for the loop comparison
  while len(pageList)>0:
    pageList = [] #reinit once inside of the loop
    params['skip']=skip
    tries = 0
    while tries<maxTries:
      try:
        r = o.requests.get(url, params=params, timeout=5).text
        pageList = r.split('j-Symbol ">')[1:]
        pageList = [e.split(">")[1][:-3] for e in pageList]
        symbList += pageList
        if(verbose): print(f"MW page {int(skip/resultsPerPage)}")
        break
      except Exception:
        tries+=1
        print(f"Error getting MW data for {algo}. Trying again...")
        o.time.sleep(3)
        continue
    skip+=len(pageList)
  
  
  
  #now that we have the marketWatch list, let's get the stocksunder1 list - essentially the getPennies() fxn from other files
  if(verbose): print("Getting stocksunder1 data...")
  #TODO: ensure prices and volumes work for all types
  urlList = ['nasdaq']#,'tech','biotech','marijuana','healthcare','energy'] #the ones not labeled for nasdaq are listed on OTC which we want to avoid
  for e in urlList:  
    if(verbose): print(e+" stock list")
    url = f'https://stocksunder1.org/{e}-penny-stocks/'
    tries=0
    while tries<maxTries:
      try:
        r = o.requests.post(url, params={"price":5,"volume":0,"updown":"up"}, timeout=5).text
        pageList = r.split('.php?symbol=')[1:]
        pageList = [e.split('">')[0] for e in pageList]
        symbList += pageList
        break
      except Exception:
        print("No connection, or other error encountered (SU1). Trying again...")
        o.time.sleep(3)
        tries+=1
        continue
    
  if(verbose): print("Removing Duplicates...")
  symbList = list(dict.fromkeys(symbList)) #combine and remove duplicates

  return symbList


#return a dict of stocks that are good to buy, format of {symb:last retest/exit date}
def goodBuys(symbList, verbose=False):
  out = {} #contains dict of {symb:note}
  sema = int(c[algo]['sema']) #get the short EMA timeframe
  lema = int(c[algo]['lema']) #get the long EMA timeframe
  timeLim = int(c[algo]['timeLim']) #only look for a crossover within this many periods (in days)
  
  for i,s in enumerate(symbList):
    if(verbose): print(f"\n({i+1}/{len(symbList)})",s)
    #get the historic prices going back to timeLim+lema for calculations (also add a little extra time in case of missed days)
    prices = o.getHistory(s,str(o.wd(o.dt.date.today(),-(timeLim+lema+5))),str(o.dt.date.today()))
    
    # calc semas and lemas within timeLim
    semaList = o.getEMAs([float(p[1]) for p in prices],sema)
    lemaList = o.getEMAs([float(p[1]) for p in prices],lema)
    
    # if(verbose): print("prices:",len(prices),"semas:",len(semaList),"lemas:",len(lemaList))
    
    # look for an ema crossover
    i=lema
    while i<timeLim and semaList[i]>lemaList[i]:
      i+=1
    #found a crossover
    if(i<timeLim):
      if(verbose): print(i,"found crossover")
      #start looking for entrances/exits
      exit1=False
      retest1=False
      exit2=False
      retest2=False
      exit3=False
      while i>=0:
        i+=1
        if(float(prices[i][5])>semaList[i] and not exit1):
          if(verbose): print(i,"exit 1")
          exit1 = True
          continue
        if(exit1):
          if(price[i][5]<lemaList[i] and not retest1):
            if(verbose): print(i,"retest 1")
            retest1 = True
            continue
          if(retest1):
            if(price[i][5]>semaList[i] and not exit2):
              if(verbose): print(i,"exit 2")
              exit2 = True
              continue
            if(exit2):
              if(price[i][5]<=semaList[i] and not retest2):
                if(verbose): print(i,"retest 2")
                retest2 = True
                continue
              if(retest2):
                if(price[i][5]>semaList[i] and not exit3):
                  if(verbose): print(i,"exit 3")
                  exit3=True
                  continue
                if(exit3):
                  if(price[i][5]<semaList[5]):
                    if(verbose): print(i,"add to buy list")
                    out[s]=price[i][0]
                    break
  
  return out

#return whether a stock is good to sell or not
def goodSells(symbList, verbose=False):
  print(f"{algo} incomplete")
  
  if(verbose): print(f"stocks in prices: {list(prices)}")
  #check that it has exceeded the stopLoss or takeProfit points
  gs = {}
  for s in symbList:
    if(s in prices):
      if(verbose): print(f"{s}\topen: {round(prices[s]['price']/prices[s]['open'],2)}\tbuy: {round(prices[s]['price']/buyPrices[s],2)}\tsellUp: {sellUp(s)}\tsellDn: {sellDn(s)}")
      #check if price triggered up
      if(prices[s]['price']/prices[s]['open']>=sellUp(s) or prices[s]['price']/buyPrices[s]>=sellUp(s)):
        gs[s] = 1
      #check if price triggered down
      elif(prices[s]['price']/prices[s]['open']<sellDn(s) or prices[s]['price']/buyPrices[s]<sellDn(s)):
        gs[s] = -1
      else: #price didn't trigger either side
        gs[s] = 0
    else:
      gs[s] = 0
  
  
  
  return False


#TODO: this should also account for squeezing
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo] #stocks held by this algo according to the records
  lock.release()
  mainSellUp = float(c[algo]['sellUp'])
  startSqueeze = float(c[algo]['startSqueeze'])
  squeezeTime = float(c[algo]['squeezeTime'])

  if(symb in stockList):
    #TODO: add exit condition (see it in goodBuys)
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo] #stocks held by this algo according to the records
  lock.release()
  mainSellDn = float(c[algo]['sellDn'])
  if(symb in stockList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

#get the stop loss for a symbol after its been triggered (default to the main value)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
