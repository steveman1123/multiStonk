#this file contains functions specifically for the exponential moving average algo
#how can we apply an ema to various stocks?
#https://tradingstrategyguides.com/exponential-moving-average-strategy/
#https://www.investopedia.com/terms/e/ema.asp
#also, an ema can work across multiple exchange types, not just for stocks
#this specific one will look at stocks over a period of days

import otherfxns as o

algo = 'ema' #name of the algo
#stocks held by this algo according to the records
# stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]


def getList():
  print(f"getting unsorted list for {algo}")
  symbs = getUnsortedList()
  print(f"finding stocks for {algo}")
  goodBuys = [e for e in symbs if goodBuy(e)] #the only time that the first char is a number is if it is a valid/good buy
  print(f"{len(goodBuys)} found for {algo}")
  return goodBuys
 

#determine whether the queries symb is a good one to buy or not
def goodBuy(symb):
  #a good buy is considered if current value is >1 stddev below ema as outlined above
  emaSper = int(o.c[algo]['emaSper'])
  emaLper = int(o.c[algo]['emaLper'])
  
  #TODO: do we want to look at minute-to-minute data rather than day-to-day? Or somewhere in between? Might be good to look at like 2 hour intervals
  hist = o.getHistory(symb) #get the history
  closeList = [e[1] for e in hist] #(isolate just the closes of hist rather than passing the whole thing)
  '''
  TODO: should look at a few things:
to buy:
look for when the Sema first > Lema
then look for first time where price is < Sema and >Lema after being above Sema, then look for second time of the same being above, then within
then buy whenever the min <=Sema

to sell:
look for when Lema>Sema, then look for the first time that the price >Sema and <Lema after being <Sema
  
  needs to generate a list/running ema rather than just a single value
  then, starting from today, loop back till we see an inversion (or up to a predetermined timeframe. If we don't see one, return false)
  if we do see one, then start looking forward. If we see the price leave, then if we see the price be <Sema & >Lema, then if we see the price leave again, then if we see the price come back again like before, then go back above, then it's a good buy
  
  https://tradingstrategyguides.com/exponential-moving-average-strategy/
  '''
  emaS = getEMA(symb,emaSper,closeList,0,float(o.c[algo]['smoothing']))  #get the ema for the short period 
  emaL = getEMA(symb,emaLper,closeList,0,float(o.c[algo]['smoothing']))  #get the ema for the long period
  
  curPrice = o.getPrice(symb)
  
  
  
  
  return (curPrice>emaL>emaS) #should be a good buy if 

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

#return whether symb is a good sell or not
def goodSell(symb):
  #needs stuff here
  return True


#TODO: this should also account for squeezing
def sellUp(symb=""):
  mainSellUp = float(o.c[algo]['sellUp'])
  if(symb in stockList):
    #TODO: add exit condition (see it in goodBuys)
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
