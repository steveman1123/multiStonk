#this file contains functions specifically for the div algo
#what changes when a stock has a dividend?
#https://www.investopedia.com/articles/stocks/11/dividend-capture-strategy.asp

import sys
sys.path.append('../') #might not need this line?

import otherfxns as o


def getList():
  #perform checks to see which one ones will gain
  #check history of the stocks. Look for pattern that denotes a gain after the initial div date (could possibly look like a buy low. Stock gains to div, div processes, dips, then gains again. Sell at that gain)
  
  return goodBuys
  


def sellUp():
  return float(cfg['divs']['sell params']['sellUp'])

def sellDn():
  return float(cfg['divs']['sell params']['sellDn'])

def sellUpDn():
  return float(cfg['divs']['sell params']['sellUpDn'])


#get a list of stocks to be sifted through
def getUnsortedList():
  while True:
    try:
      r = o.json.loads(o.requests.get("https://api.nasdaq.com/api/calendar/dividends",headers={"user-agent":"-"}, timeout=5))['data']['rows']
      break
    except Exception:
      print("Error in getting unsorted list for divs algo. Trying again...")
      o.time.sleep(3)
      pass
  return r
