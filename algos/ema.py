#this file contains functions specifically for the exponential moving average algo
#how can we apply an ema to various stocks?
#https://www.alphaexcapital.com/ema-trading-strategy/
#https://www.investopedia.com/terms/e/ema.asp
#also, an ema can work across multiple exchange types, not just for stocks
#these we want to look for high variance, or else for ones that follow a predictable curve (for 

import otherfxns as o

algo = 'ema' #name of the algo
#stocks held by this algo according to the records
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]


def getList():
  print(f"getting unsorted list for {algo}")
  symbs = getUnsortedList()
  print(f"finding stocks for {algo}")
  goodBuys = [e for e in symbs if goodBuy(e)] #the only time that the first char is a number is if it is a valid/good buy
  print(f"{len(goodBuys)} found for {algo}")
  return goodBuys
 
'''
8 different 'goodBuy' states:
is >1 stdev below ema(L/M/S)

LMS 
'''


#determine whether the queries symb is a good one to buy or not
def goodBuy(symb):
  #a good buy is considered if current value is >1 stddev below ema
  
  
  
  return isGoodBuy



#get a list of stocks to be sifted through
def getUnsortedList():
  return []

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
