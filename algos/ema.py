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

def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}")
  symbs = getUnsortedList()
  if(verbose): print(f"{len(symbs)} potential gainers for {algo}")
  if(verbose): print(f"finding stocks for {algo}")
  goodBuys = {s:"" for s in symbs if goodBuy(s)} #add note here if we want one
  if(verbose): print(f"{len(goodBuys)} found for {algo}")
  return goodBuys
 
#TODO: port from goodBuy
def goodBuys(symbList):
  print(f"{algo} incomplete")
  return False

#TODO: port from goodSell
def goodSells(symbList):
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

#determine whether the queries symb is a good one to buy or not
def goodBuy(symb, verbose=False):
  
  emaSper = int(c[algo]['emaSper']) #period length of the short EMA (typically 8 or 9 or 20)
  emaLper = int(c[algo]['emaLper']) #period length of the long EMA (typically 20, 50 or 200)
  timeLim = int(c[algo]['timeLim']) #days to look back for the EMA crossover
  testNum = int(c[algo]['testNum']) #number of EMA tests to limit at (where the price exits and re-enteres the sema/lema range)
  
  
  #get the short and long period EMAs
  sema = getEMAs(symb,str(wd(o.dt.date.today(),-(timeLim+2))),str(o.dt.date.today()),emaSper)
  lema = getEMAs(symb,str(wd(o.dt.date.today(),-(timeLim+2))),str(o.dt.date.today()),emaLper)
  price = [float(e[1]) for e in o.getHistory(symb,str(wd(o.dt.date.today(),-(timeLim+2))),str(o.dt.date.today()))] #get the closing prices of the stock
  
  if(len(sema)<=timeLim):
    if(verbose): print(f"Not enough data for {symb}")
    return False
  
  #look for the crossover when sema > lema (ensure that we stay within range and timeLimit)
  daysBack = 0
  while(daysBack<min(len(sema),len(lema)) and (daysBack<timeLim or sema[daysBack]<lema[daysBack])):
    daysBack += 1
  
  #if it is
  if(sema[daysBack]>lema[daysBack]):
    daysFor = daysBack
    tests = 0
    priceAboveRangeSinceLastTest = False
    priceInRangeSinceLastExit = False
    while daysFor>0: #start moving forward in time from the inversion point back to today
      #TODO: these conditionals could probably stand to be cleaned up a bit
      
      #if the price is above the EMA range
      if(price[daysFor]>sema[daysFor]):
        priceAboveRangeSinceLastTest = True
        priceInRangeSinceLastExit = False
      #else if the price is within the EMA range (and the )
      elif(lema[daysFor]<price[daysFor]<sema[daysFor] and priceAboveRangeSinceLastTest):
        priceAboveRangeSinceLastTest = False
        priceInRangeSinceLastExit = True
      
      if(priceInRangeSinceLastExit):
        tests += 1
        priceAboveRangeSinceLastTest = False
        priceAboveRangeSinceLastTest = False
      
      daysFor -= 1
      
    if(tests<testNum):
      if(verbose): print(f"Not enough tests for {symb}")
      return False
    elif(tests>testNum):
      if(verbose): print(f"Too many tests for {symb}")
      return False
    else:
      if(verbose): print(f"{testNum} tests found for {symb}")
      return True
  else:
    if(verbose): print(f"No EMA crossover for {symb}")
    return False
  
  '''
  TODO: should look at a few things:
to buy:
look for when the Sema first > Lema
then look for first time where price is < Sema and >Lema after being above Sema, then look for second time of the same being above, then within
then buy whenever the min <=Sema

  
x  needs to generate a list/running ema rather than just a single value
x  then, starting from today, loop back till we see an inversion (or up to a predetermined timeframe. If we don't see one, return false)
x  if we do see one, then start looking forward. If we see the price leave, then if we see the price be <Sema & >Lema, then if we see the price leave again, then if we see the price come back again like before, then go back above, then it's a good buy
  
  https://tradingstrategyguides.com/exponential-moving-average-strategy/
  '''
  
#return whether symb is a good sell or not
def goodSell(symb, verbose=False):
  #to sell: look for when Lema>Sema, then look for the first time that the price >Sema and <Lema after being <Sema
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo] #stocks held by this algo according to the records
  lock.release()
  
  #mark to sell (just in case it's not caught somewhere else)
  if(symb in stockList):
    if(stockList[symb]['shouldSell']):
      return True
  
  emaSper = int(c[algo]['emaSper']) #period length of the short EMA (typically 8 or 9 or 20)
  emaLper = int(c[algo]['emaLper']) #period length of the long EMA (typically 20, 50 or 200)
  timeLim = int(c[algo]['timeLim']) #days to look back for the EMA crossover
  
  [startDate,endDate] = [str(wd(o.dt.date.today(),-(timeLim+2))), str(o.dt.date.today())] #define the date ranges
  lema = getEMAs(symb,startDate,endDate,emaLper) #get the long period EMA
  sema = getEMAs(symb,startDate,endDate,emaSper) #get the short period EMA
  price = [float(e[1]) for e in o.getHistory(symb,startDate,endDate)] #get the closing prices of the stock
  
  #this should never be triggered because we shouldn't've been able to buy in the first place then
  if(len(sema)<=timeLim):
    if(verbose): print(f"Not enough data for {symb}")
    return True
  
  #look for the crossover when lema > sema again
  daysBack = 0
  while(daysBack<timeLim or sema[daysBack]>lema[daysBack]):
    daysBack += 1
  
  if(sema[daysBack]<lema[daysBack]):
    daysFor = daysBack
    tests = 0
    priceBelowRangeSinceLastTest = False
    while daysFor>0: #start moving forward in time from the reversion point back to today
      #TODO: these conditionals could probably stand to be cleaned up a bit
      
      #if the price is above the EMA range
      if(price[daysFor]<sema[daysFor]):
        priceBelowRangeSinceLastTest = True
      #else if the price is within the EMA range (and the )
      elif(lema[daysFor]>price[daysFor]>sema[daysFor] and priceBelowRangeSinceLastTest):
        return True
      
      daysFor -= 1
    
    if(verbose): print("exit test not hit yet")
    return False
    
  else:
    if(verbose): print("reversion has not occurred yet")
    return False
    
  
#where closelist has the most recent close first (and is the EMA that is being calculated)
def getEMA(priceList,k):
  if(len(priceList)>1):
    return (priceList[0]*k)+(getEMA(priceList[1:],k)*(1-k))
  else:
    return priceList[0]
  
#get the EMAs for all prices in a given set
# where priceList is the list that the EMAs should be gotten for, and n is the length of the ema
# https://www.dummies.com/personal-finance/investing/stocks-trading/how-to-calculate-exponential-moving-average-in-trading/
def getEMAs(symb,startDate,endDate,n):
  k = 2/(1+n)
  extraDays = 0 #add in some more days to get a better reading of the earlier EMAs
  
  hist = o.getHistory(symb,str(o.dt.datetime.strptime(startDate,"%Y-%m-%d").date()-o.dt.timedelta(extraDays)),endDate)
  totalEntries = len(o.getHistory(symb,str(o.dt.datetime.strptime(startDate,"%Y-%m-%d").date()),endDate))
  
  #isolate the closing prices
  priceList = [float(e[1]) for e in hist]
  
  out = []
  for i in range(len(priceList)):
    out.append(getEMA(priceList[i:],k))
  #TODO: might have to check that enough data was returned?
  return out[:totalEntries] #trim off extra days


#get a list of stocks to be sifted through
def getUnsortedList(verbose=False):
  symbList = []

  if(verbose): print("Getting MarketWatch data...")
  url = 'https://www.marketwatch.com/tools/stockresearch/screener/results.asp'
  params = {
            "submit":"Screen",
            "Symbol":"true",
            "ResultsPerPage":"OneHundred",
            "TradesShareEnable":"true",
            "TradesShareMin":c[algo]['minPrice'],
            "TradesShareMax":c[algo]['maxPrice'],
            "TradeVolEnable":"true",
            "TradeVolMin":c[algo]['minVol'],
            "Exchange":"NASDAQ"
            }
  params['PagingIndex'] = 0 #this will change to show us where in the list we should be - increment by 100 (see ResultsPerPage key)

  while True:
    try:
      r = o.requests.get(url, params=params, timeout=5).text
      totalStocks = int(r.split("matches")[0].split("floatleft results")[1].split("of ")[1]) #get the total number of stocks in the list - important because they're spread over multiple pages
      break
    except Exception:
      print("No connection or other error encountered in getList (MW). Trying again...")
      time.sleep(3)
      continue
      
  for i in range(0,totalStocks,100): #loop through the pages (100 because ResultsPerPage is OneHundred)
    if(verbose): print(f"page {int(i/100)+1} of {o.ceil(totalStocks/100)}")
    params['PagingIndex'] = i
    while True:
      try:
        r = o.requests.get(url, params=params, timeout=5).text
        break
      except Exception:
        print("No connection or other error encountered in getList (MW). Trying again...")
        time.sleep(3)
        continue

    try:
      table = o.bs(r,'html.parser').find_all('table')[0]
      for e in table.find_all('tr')[1::]:
        symbList.append(e.find_all('td')[0].get_text())
    except Exception:
      print("Error in MW website.")
    
  return symbList


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
