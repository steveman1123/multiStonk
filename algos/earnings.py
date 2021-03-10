#this file contains functions specifically for the earnings
#what happens to a stock after various earnings calls?

import sys
sys.path.append('../') #might not need this line?

import otherfxns as o


def getList():
  #perform checks to see which one ones will gain
  
  
  return goodBuys
  

#get a list of stocks to be sifted through
def getUnsortedList():
  while True:
    try:
      r = o.json.loads(o.requests.get("https://api.nasdaq.com/api/calendar/earnings",headers={"user-agent":"-"}, timeout=5))['data']['rows']
      break
    except Exception:
      print("Error in getting unsorted list for earnings algo. Trying again...")
      o.time.sleep(3)
      pass
  return r
