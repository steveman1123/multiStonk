#functions specific to algo2
import sys
sys.path.insert(0,'../common')
# import alpacafxns as a
import otherfxns as o
import time,json



'''
potentially useful links:
https://www.dummies.com/personal-finance/investing/penny-stocks/9-signs-that-penny-stock-is-about-to-rise/
https://pennystocks.com/featured/2020/09/20/5-high-volume-penny-stocks-to-watch-this-week-september-20-2020/
'''



#get company symbols from drugs.com new applications
def getDrugList():
  while True:
    try:
      r = a.o.requests.get("https://www.drugs.com/new-drug-applications.html", timeout=5).text
      break
    except Exception:
      print("Connection error, trying again...")
      time.sleep(3)
      continue
  try:
    arr = r.split("Company:</b>")
    arr = [e.split("<br>")[0].strip() for e in arr][1::]
  except Exception:
    print("Bad data")
    arr = []

  list(set(arr)) #remove duplicates
  
  #convert company names to stock symbols and onlly return the ones on nasdaq
  out = []
  for e in arr:
    inf = o.getSymb(e)
    if(inf[1] in ['NAS','NSD']): #different nasdaq abbreviations depending on what url is used in getSymb()
      out += [inf[0]]
  
  return out

#get positions currently held by this algo
def getPos(historyFile):
  with open(historyFile,'r') as f:
    allPos = json.loads(f.read())
    pos = [p for p in allPos if p[latestDate]['tradeType']=='buy']
  return pos

def getHist(pos,historyFile):
  with open(historyFile,'r') as f:
    hist = json.loads(f.read())[pos]
  return hist