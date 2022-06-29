#this file contains functions specifically for the exponential moving average algo
#how can we apply an ema to various stocks?
#https://www.alphaexcapital.com/ema-trading-strategy/
#https://www.investopedia.com/terms/e/ema.asp
#also, an ema can work across multiple exchange types, not just for stocks
#this specific one will look at stocks over a period of minutes/hours

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

def getList():
  print(f"getting unsorted list for {algo}")
  symbs = getUnsortedList()
  print(f"finding stocks for {algo}")
  goodBuys = {e:"" for e in symbs if goodBuy(e)} #return dict of symb:note
  print(f"{len(goodBuys)} found for {algo}")
  return goodBuys
 
'''
8 different 'goodBuy' states:
is >1 stdev below ema(L/M/S)

LMS isGoodBuy
000 0
001 1
010 1
011 1
100 1
101 1
110 1
111 1

S(M+L)
'''
#determine whether the queries symb is a good one to buy or not
def goodBuy(symb):
  #a good buy is considered if current value is >1 stddev below ema as outlined above
  emaSper = int(o.c[algo]['emaSper'])
  emaLper = int(o.c[algo]['emaLper'])
  
  #TODO: do we want to look at minute-to-minute data rather than day-to-day? Or somewhere in between? Might be good to look at like 2 hour intervals
  hist = o.getShortHistory(symb) #get the history just over the long ema days to look
  if(len(hist)<emaLper): #TODO: the length should always be longer than this. See the prev line for how long it actually should be
    print(f"Not enough data for {symb}")
    return False

  closeList = [e[1] for e in hist] #(isolate just the closes of hist rather than passing the whole thing)

  emaS = getEMA(symb,emaSper,closeList,0,float(o.c[algo]['smoothing']))  #get the ema for the short period 
  emaL = getEMA(symb,emaLper,closeList,0,float(o.c[algo]['smoothing']))  #get the ema for the long period

  curPrice = o.getPrice(symb)
  
  if()
  
  
  return (curPrice>emaL>emaS) #should be a good buy if 


def goodSells(symbList, verbose=False):
  print("algo incomplete")
  
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

#calculating the ema is a recursive function
def getEMA(symb,totalDays,closeList,daysAgo,smoothing):
  #ema(today) = (price*(smoothing/(1+days)))+ema(yesterday)*(1-(smoothing/(1+days)))
  if(daysAgo<=totalDays):
    emaYest = getEMA(symb,totalDays,closeList,daysAgo+1,smoothing)
    return (float(closeList[daysAgo])*(smoothing/(1+totalDays)))+emaYest*(1-(smoothing/(1+totalDays)))
  else:
    return float(closeList[daysAgo])

#get a list of stocks to be sifted through
def getUnsortedList():
  symbList = []

  print("Getting MarketWatch data...")
  url = 'https://www.marketwatch.com/tools/stockresearch/screener/results.asp'
  params = {
            "submit":"Screen",
            "Symbol":"true",
            "ResultsPerPage":"OneHundred",
            "TradesShareEnable":"true",
            "TradesShareMin":o.c[algo]['minPrice'],
            "TradesShareMax":o.c[algo]['maxPrice'],
            "TradeVolEnable":"true",
            "TradeVolMin":o.c[algo]['minVol'],
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
    print(f"page {int(i/100)+1} of {o.ceil(totalStocks/100)}")
    params['PagingIndex'] = i
    while True:
      try:
        r = o.requests.get(url, params=params, timeout=5).text
        break
      except Exception:
        print("No connection or other error encountered in getList (MW). Trying again...")
        time.sleep(3)
        continue

    table = o.bs(r,'html.parser').find_all('table')[0]
    for e in table.find_all('tr')[1::]:
      symbList.append(e.find_all('td')[0].get_text())
  
  return symbList




#TODO: this should also account for squeezing
def sellUp(symb=""):
  mainSellUp = float(o.c[algo]['sellUp'])
  if(symb in stockList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  mainSellDn = float(o.c[algo]['sellDn'])
  if(symb in stockList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(o.c[algo]['sellUpDn'])
