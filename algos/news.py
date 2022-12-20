#this file contains functions specifically for the news algo
#what changes when a stock has news written about it, what about the sentiment of that news?

#TODO: populate goodBuys, goodSells, and getUnsortedList

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name


def init(configFile):
  global c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

#return dict of {symb:note} where the note is payment date and div amount, formatted as "yyyy-mm-dd, $.$$"
def getList(verbose=True):
  
  #perform checks to see which one ones will gain
  #check history of the stocks. Look for pattern that denotes a gain after the initial div date (could possibly look like a buy low. Stock gains to div, div processes, dips, then gains again. Sell at that gain)
  
  #if today < ex div date, then buy
  if(verbose): print(f"getting unsorted list for {algo}...")
  ntt = o.dt.datetime.strptime(o.nextTradeDate(),"%Y-%m-%d").date() #get the next trade date as a date type
  ul = getUnsortedList([str(ntt),str(o.wd(ntt,1))]) #get the whole data lists for the specified dates (next trade date and the following day after that
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
  if(verbose): print(f"finding stocks for {algo}...")
  gb = goodBuys(ul)
  if(verbose): print(f"{len(gb)} found for {algo}.")
  return gb
  

#determine if a list of stocks are good to sell or not
#where symblist is a list of stocks and the function returns the same stocklist as a dict of {symb:goodsell(t/f)}
def goodSells(symbList, verbose=False):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  buyPrices = {e:posList[e]['buyPrice'] for e in posList} #get the prices each were bought at
  symbList = [e for e in symbList if e in posList] #make sure they're the ones in the posList only
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  gs = {}
  for s in symbList:
    if(s in prices):
      if(verbose): print(f"{s}\topen: {round(prices[s]['price']/prices[s]['open'],2)}\tbuy: {round(prices[s]['price']/buyPrices[s],2)}\tsellUp: {sellUp(s)}\tsellDn: {sellDn(s)}")
      #check if price triggered up
      if(prices[s]['open']>0 and buyPrices[s]>0):
        if(prices[s]['price']/prices[s]['open']>=sellUp(s) or prices[s]['price']/buyPrices[s]>=sellUp(s)):
          gs[s] = 1
        #check if price triggered down
        elif(prices[s]['price']/prices[s]['open']<sellDn(s) or prices[s]['price']/buyPrices[s]<sellDn(s)):
          gs[s] = -1
        else: #price didn't trigger either side
          gs[s] = 0
      else:
        gs[s] = 0
    else:
      gs[s] = 0
  
  
  return gs

#get the list of stocks to sort through
def getUnsortedList(maxTries=3):
  out = {}
  
  return out

#where symbList is the output of getUnsortedList
#returns dict of stocks that are good to buy - format of {symb:note} where the note is formatted as ???
def goodBuys(symbList, verbose=False):
  if(verbose): print(f"{len(symbList)} found for news")
  gb={}
  
  return gb



#determine how much the take-profit should be for change since buy or change since close
def sellUp(symb="",verbose=False):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

  if(symb in posList):
    return float(c[algo]['sellUp'])
  else:
    if(verbose): print(f"{symb} not in posList of {algo}")
    return float(c[algo]['sellUp'])

#determine how much the stop-loss should be for change since buy or change since close
def sellDn(symb="",verbose=False):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

  if(symb in posList):
    return float(c[algo]['sellDn'])
  else:
    if(verbose): print(f"{symb} not in posList of {algo}")
    return float(c[algo]['sellDn'])

#after triggering the take-profit, the price must fall this much before selling (rtailing stop-loss)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
