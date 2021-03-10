#this file contains functions specifically for the forex algo
#best way to trade currencies?
#TODO: make sure we can access the market via either alpaca or etrade
#https://www.dailyfx.com/technical-analysis
#in the event that etrade doesn't work, try this one: https://www.forex.com/en-us/trading-platforms/more-services/api-trading/

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


def curInfo(cur):
  '''
  known currencies:
  EURUSD
  USDCAD
  USDMXN
  USDCHF
  USDJPY
  USDRUB
  AUDUSD
  GBPUSD
  USDBRL
  '''
  while True:
    try:
      r = o.json.loads(o.requests.get(f"https://api.nasdaq.com/api/quote/{cur}/info?assetclass=currencies",headers={'user-agent':'-'},timeout=5))
      break
    except Exception:
      print("err")
      o.time.sleep(3)
      pass
  
  
