#this file contains functions specifically for the exponential moving average algo
#how do stocks move before and after an ipo (and/or spo?)?

# https://www.investopedia.com/a-simple-technique-to-profit-from-ipos-5078487
# https://www.tradingpedia.com/ipo-and-spo/

import otherfxns as o

algo = 'ipos' #name of the algo
#stocks held by this algo according to the records
lock = o.threading.Lock()
lock.acquire()
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]
lock.release()

def getList(verbose=True):
  if(verbose): print(f"Getting unsorted list for {algo}")
  ul = getUnsortedList() #TODO: do we also want to look at spo's, and should we focus on only one type?
  #perform checks to see which one ones will gain
  
  #may need to read the news regarding it
  
  return goodBuys #return dict of symb:note
  

#get a list of stocks to be sifted through
#type can be spo, status can be priced|upcoming|filled|withdrawn
def getUnsortedList(status="all", type=""):
  while True:
    try:
      r = o.json.loads(o.requests(f"https://api.nasdaq.com/api/ipo/calendar?type={type}",headers={"user-agent":'-'},timeout=5).text)
      break
    except Exception:
      print("Error getting unsorted list for ipo algo. Trying again...")
      o.time.sleep(3)
      pass
  
  return r['data'] if(status=="all") else r['data'][status]


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
