#this file contains functions specifically for the FDA drug approval algo
#we can see which companies are slated for an FDA drug approval. They almost always gain

#import sys
#sys.path.append('../') #might not need this line?

import otherfxns as o
#TODO: change file location to be from config file
#total stocks held by this algo
stockList = o.json.loads(open('../stockStuff/posList.json','r').read())['fda']

#get list of stocks pending FDA approvals
def getList():
  print('getting unsorted list for fda')
  while True: #get page of pending stocks
    try:
      r = o.requests.get("https://www.drugs.com/new-drug-applications.html", timeout=5).text
      #TODO: use in conjunction with this list too: https://www.biopharmcatalyst.com/calendars/fda-calendar
      break
    except Exception:
      print("No connection, or other error encountered in getDrugList. trying again...")
      o.time.sleep(3)
      continue
  print('getting unsorted list for dj')
  try:
    arr = r.split("Company:</b>") #go down to stock list
    arr = [e.split("<br>")[0].strip() for e in arr][1::] #get list of companies
    arr = [o.getSymb(e) for e in arr] #get the symbols and exchanges of the companies
    arr = [e[0] for e in arr if e[1]=="NAS"] #get the nasdaq only ones
  except Exception:
    print("Bad data")
    arr = []
  
  print(f"{len(arr)} found for fda.")
  #refine to max price (note, as of this time, this has not been tested)
  # arr = [e for e in arr if a.getPrice(e)<=float(o.c['fda']['maxPrice'])]
  #TODO: check for price changes iver the past few days/weeks
  
  return arr

#TODO: this should also account for squeezing
def sellUp(symb=""):
  mainSellUp = float(o.c['fda']['sellUp'])
  if(symb in stockList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  mainSellDn = float(o.c['fda']['sellDn'])
  if(symb in stockList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(o.c['fda']['sellUpDn'])

def maxPrice():
  return float(o.c['fda']['maxPrice'])
