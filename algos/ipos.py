#this file contains functions specifically for the exponential moving average algo
#how do stocks move before and after an ipo (and/or spo?)?

import sys
sys.path.append('../') #might not need this line?

import otherfxns as o


def getList():
  #perform checks to see which one ones will gain
  
  #may need to read the news regarding it
  
  return goodBuys
  

#get a list of stocks to be sifted through
#type can be spo, status can be priced|upcoming|filled|withdrawn
def getUnsortedList(status="all", type=""):
  while True:
    try:
      r = o.json.loads(o.requests(f"https://api.nasdaq.com/api/ipo/calendar?type={type}",headers={"user-agent":'-'},timeout=5).text)
      break
    except Exception:
      print("Error getting unsorted list for ipo algo. Trying again...")
      o.time.sleep(3)
      pass
  
  return r['data'] if(status=="all") else r['data'][status]
