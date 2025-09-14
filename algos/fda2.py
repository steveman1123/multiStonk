#this algo looks to do the following:
'''
scrape websites of companies to look for employees from FDA
$ spent on lobbying
market cap

Talk to Emily more about other info that might be useful
'''

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

def getList(verbose=True):
  print("copy from another algo")
  return False
  
  
  
  
  return gb #return dict of symb:note

#return whether stocks are good purchases or not
def goodBuys(symbList):
  print("incomplete, check which stocks are good to buy here")
  exit()
  arr = [(e+"|stocks").upper() for e in list(set(symbList))] #remove duplicates and append the |stocks label
  prices = o.getPrices(arr) #get the current prices
  

  #narow down to stocks only within our price range
  goodBuys = [e.split("|")[0] for e in arr if(e in prices and float(c[algo]['minPrice'])<prices[e]['price']<float(c[algo]['maxPrice']))]
  #probably should do more logic after this
  
  
  outs = {s:(s in goodBuys) for s in symbList} #return dict of symb:goodBuy
  
  return outs
  
#determine if stocks are good to sell or not
def goodSells(symbList):
  print(f"{algo} incomplete")
  return {s:0 for s in symbList}

#return whether symb is a good sell or not
def goodSell(symb):
  print(f"{algo} incomplete")
  return False

#get a list of stocks to be sifted through
def getUnsortedList(verbose=False):
  if(verbose): print(f"{algo} getting stocks from biopharmcatalyst.com")
  print("incomplete get stocks here")
  return False



#TODO: this should also account for squeezing
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  mainSellUp = float(c[algo]['sellUp'])
  if(symb in posList):
    #TODO: add exit condition (see it in getList)
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  mainSellDn = float(c[algo]['sellDn'])
  if(symb in posList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  
  return float(c[algo]['sellUpDn'])
