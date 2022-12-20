#this file contains functions specifically for the ease of movement algo
#what changes when a stock has a high volume breakout? Can we see when that will happen? (also check earnings report)
# https://therobusttrader.com/volume-indicators-volume-trading/


import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name


def getList(verbose=True):
  #perform checks to see which one ones will gain
  
  # If the price is rising in an uptrend but the volume is reducing or unchanged, it may show that there's little interest in the security, and the price may reverse. Similarly, when the price is rapidly declining but the volume is low, it could mean that the institutional traders are not interested in the price direction. So the price will soon reverse to the upside.
  
  
  return goodBuys #return dict of symb:note
  
def goodSells(symbList, verbose=False):
  print("incomplete")
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