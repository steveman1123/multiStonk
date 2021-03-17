#this file contains functions specifically for the FDA drug approval algo
#we can see which companies are slated for an FDA drug approval. They almost always gain

import otherfxns as o

algo = 'fda' #name of the algo
#stocks held by this algo according to the records
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]

#get list of stocks pending FDA approvals
def getList():
  print('getting unsorted list for fda')
  while True: #get page of pending stocks
    try:
      r = o.requests.get("https://www.drugs.com/new-drug-applications.html", timeout=5).text
      #r1 = o.requests.get("https://biopharmacatalyst.c8m/calendars/fda-calendar",timeout=5).text
      #TODO: use in conjunction with this list too: https://www.biopharmcatalyst.com/calendars/fda-calendar
      break
    except Exception:
      print("No connection, or other error encountered in getDrugList. trying again...")
      o.time.sleep(3)
      continue

  print(f"finding stocks for {algo}")
  try:
    arr = r.split("Company:</b>") #go down to stock list
    arr = [e.split("<br>")[0].strip() for e in arr][1::] #get list of companies
    arr = [o.getSymb(e) for e in arr] #get the symbols and exchanges of the companies
    arr = [e[0] for e in arr if e[1]=="NAS"] #get the nasdaq only ones
  except Exception:
    print("Bad data from drugs.com")
    arr = []

  '''
  try:
    arr1 = #get stock list
    #get symbols from list
    #get only the nasdaq listed ones
    print(arr1)
  except Exception:
    print("Bad data from biopharmacatalyst.com")
    arr1 = []
  '''
  print(f"{len(arr)} found for fda.")
  #refine to max price (note, as of this time, this has not been tested)
  # arr = [e for e in arr if a.getPrice(e)<=float(o.c[algo]['maxPrice'])]
  #TODO: check for price changes iver the past few days/weeks
  
  return arr

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

def maxPrice():
  return float(o.c[algo]['maxPrice'])
