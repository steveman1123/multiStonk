#this file contains functions specifically for the gap up algo
#what is a gap up, and how can we see it coming?
#https://www.investopedia.com/articles/trading/05/playinggaps.asp
#https://bullsonwallstreet.com/how-to-know-if-a-stock-gap-up-will-fade-or-explode/

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name


def getList(verbose=True):
  #perform checks to see which one ones will gain
  
  
  return goodBuys #return dict of symb:note
  
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
