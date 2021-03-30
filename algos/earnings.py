#this file contains functions specifically for the earnings
#what happens to a stock after various earnings calls?

# https://tradingreviews.net/why-stock-prices-fall-after-good-earnings-announcements
# https://www.marketwatch.com/story/heres-how-to-trade-a-stock-after-an-earnings-surprise-2016-08-18
# https://finance.zacks.com/impact-earnings-announcements-stock-prices-4265.html
# https://www.investopedia.com/terms/e/earningssurprise.asp


import otherfxns as o

algo = 'earnings' #name of the algo
#stocks held by this algo according to the records
lock = o.threading.Lock()
lock.acquire()
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]
lock.release()

def getList(verbose=True):
  #perform checks to see which one ones will gain
  maxPrice =
  minPrice = 

#https://seekingalpha.com/article/1445911-a-remarkably-reliable-way-to-predict-post-earnings-price-moves
  
  return goodBuys
  

#get a list of stocks to be sifted through
def getUnsortedList():
  while True:
    try:
      r = o.json.loads(o.requests.get("https://api.nasdaq.com/api/calendar/earnings",headers={"user-agent":"-"}, timeout=5))['data']['rows']
      break
    except Exception:
      print("Error in getting unsorted list for earnings algo. Trying again...")
      o.time.sleep(3)
      pass
  return r

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
