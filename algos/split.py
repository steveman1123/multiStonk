#this file contains functions specifically for the splits algo
#what changes when a stock splits?

# https://ezinearticles.com/?How-to-Trade-Stock-Splits-the-Easy-Way&id=1959978
# http://www.rightline.net/education/stagesofsplit.html

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

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

def getList(verbose=True):
  #perform checks to see which one ones will gain
  if(verbose): print(f"Getting unsorted list for {algo}")
  ul = getUnsortedList()
  if(verbose): print("Finding splits")



  if(verbose): print("Checking history")
  #TODO: see what causes momentum to pick up and when a good time to sell may be
  
  return goodBuys #return dict of symb:note
  
#check if something is a good one to buy (symbObj is the data returned per row in get unsortedList)
def goodBuy(symbObj):
  #make sure that the split is valid (not % or reverse split)
    try: #normally the data is formatted as # : # as the ratio, but sometimes it's a %
      ratio = symbObj['ratio'].split(" : ")
      ratio = float(ratio[0])/float(ratio[1])
    except Exception: #this is where it'd go if it were a %
      ratio = 0
  
  
  if(ratio>1 and (float(c[algo]['maxDays'])>=o.dt.timefstr(symbObj['executionDate'],"%m/%d/%Y")-o.dt.date.today()).days>=float(c[algo]['daysBeforeExec'])):
    # If a stock starts to rise about two weeks before the split then this is a good candidate to buy.
    hist = o.getHistory(symbObj['symbol'],str(o.dt.date.today()-o.dt.timedelta(7*float(c[algo]['compWks']))),str(o.dt.date.today()))
    closeList = [e[1] for e in hist]
    avgClose = sum(closeList)/len(closeList)
    curPrice = o.getPrice(symbObj['symbol'])
    if(curPrice>closeList[-1] and curPrice>avgClose):
      if(verbose): print(f"{symbObj['symbol']} is a good buy")
      return True
    else:
      if(verbose): print(f"Current price is less than yesterday or less than {c[algo]['compWks]} avg")
      return False
  else:
    if(verbose): print("Ratio under 1 or too close to execution date")
    return False
    
  #if today is within a certain timeframe of the split (more than 1 week, less than 2?)
    #get the history for a little bit before today
    # if(currentPrice>yesterdayPrice and curPrice>avgofhist):  
      # return True
  #   else:
  #     return False
  # else: return False
  

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


#get a list of stocks to be sifted through
def getUnsortedList():
  while True: #get page of upcoming stock splits
    try:
      r = o.json.loads(o.requests.get("https://api.nasdaq.com/api/calendar/splits", headers={"user-agent":"-"}, timeout=5).text)['data']['rows']
      break
    except Exception:
      print("No connection, or other error encountered in reverseSplitters. trying again...")
      time.sleep(3)
      continue
  return r

#TODO: this should also account for squeezing and the price change post split (should look at total p/l rather than per stock)
def sellUp(symb=""):
  mainSellUp = float(c[algo]['sellUp'])
  if(symb in posList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  mainSellDn = float(c[algo]['sellDn'])
  if(symb in posList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(c[algo]['sellUpDn'])
