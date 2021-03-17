#this file contains functions specifically for the gap up algo
#what is a gap up, and how can we see it coming?
#https://www.investopedia.com/articles/trading/05/playinggaps.asp
#https://bullsonwallstreet.com/how-to-know-if-a-stock-gap-up-will-fade-or-explode/

import otherfxns as o

algo = 'gapup' #name of the algo
#stocks held by this algo according to the records
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]

def getList():
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
