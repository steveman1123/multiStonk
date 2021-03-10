#this file contains functions specifically for the splits algo
#what changes when a stock splits?
import sys
sys.path.append('../') #might not need this line?

import otherfxns as o


def getList():
  #perform checks to see which one ones will gain
  
  
  return goodBuys
  

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