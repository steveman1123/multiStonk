#this file contains functions specifically for the fibonacci retracemnet algo
# https://www.investopedia.com/articles/active-trading/091114/strategies-trading-fibonacci-retracements.asp
# https://www.investopedia.com/articles/markets/010515/use-fibonacci-point-out-profitable-trades.asp
# https://tradingsim.com/blog/fibonacci-trading/

import otherfxns as o

algo = 'fibo' #name of the algo
#stocks held by this algo according to the records


def getList(verbose=True):
  #perform checks to see which one ones will gain
  
  
  return goodBuys
  


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


#get a list of stocks to be sifted through
def getUnsortedList():
  return []