#this file contains functions specifically for the stocks that are listed in investopedia - these are probably updated monthly
# https://www.investopedia.com/updates/top-penny-stocks/

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

def init(configFile):
  global posList,c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())
  if(algo in posList):
    posList = posList[algo]
  else:
    posList = {}
  lock.release()


#return a dict of good buys {symb:note}
#the note contains the overall change %
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"finding stocks for {algo}...")
  arr = goodBuys(ul) #returns dict of {symb:gooduy(t/f)}
  arr = {e:ul[e] for e in arr if(arr[e])} #only look at the ones that are true
  if(verbose): print(f"{len(arr)} found for {algo}.")
  
  return arr

#multiplex the goodBuy fxn (symbList should be the output of getUnsortedList)
#return dict of {symb:t/f}
def goodBuys(symbList):
  #TODO: check prices and other info investopedia may have (plus cross reference with other sites)
  gb = {s:True for s in symbList}
  return gb

#multiplex the good sell function to return dict of {symb:t/f}
def goodSells(symbList,verbose=False):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  symbList = [e.upper() for e in symbList if e.upper() in posList] #make sure they're the ones in the posList only
  buyPrices = {e:float(posList[e]['buyPrice']) for e in symbList} #get the prices each stock was bought at
  if(verbose): print(f"stocks in the buyPrices: {list(buyPrices)}")
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  if(verbose): print(f"stocks in prices: {list(prices)}")
  #check that it has exceeded the stopLoss or takeProfit points
  #ensure recorded prices are >0 (avoid div0)
  gs = {s:(s not in prices or buyPrices[s]==0 or prices[s]['price']==0 or
           prices[s]['price']/prices[s]['open']>=sellUp(s) or
           prices[s]['price']/prices[s]['open']<sellDn(s) or
           prices[(s)]['price']/buyPrices[s]<sellDn(s) or
           prices[(s)]['price']/buyPrices[s]>=sellUp(s)
          ) for s in symbList}
  
  return gs

#get a list of stocks to be sifted through - returns dict of {symb:"date, type"}

def getUnsortedList(verbose=False,maxTries=3):
  out = {}
  
  #get the top penny stocks
  tries=0
  while tries<maxTries:
    try:
      r = o.requests.get("https://www.investopedia.com/updates/top-penny-stocks/",headers=o.HEADERS,timeout=5).text #get the data
      d = r.split('displayed-date_1-0')[1].split("<")[0].split("Updated ")[1] # isolate the last updated date
      d = str(o.dt.datetime.strptime(d,"%b %d, %Y").date()) #convert from "mmm d, yyyy" to "yyyy-mm-dd"
      r = [e for e in r.split("<") if e.startswith("span")] #only use spans (other acronyms can appear in the paragraphs, and we don't want those)
      symbList = o.re.findall("\([A-Z]+\)", "".join(r)) #convert list back to string and pare down to wanted strings (the acronyms)
      symbList = {e[1:-1]:d+", top" for e in symbList} #trim off parens and convert to dict {symb:"date, type"}
      out.update(symbList) #append to output
      break
    except Exception:
      print("Error encoutered getting investopedia top penny stocks. Trying again...")
      if(verbose): print(f"{tries}/{maxTries}")
      tries+=1
      o.time.sleep(3)  
  
  
  #get the technical analysis stocks
  tries=0
  while tries<maxTries:
    try:
      r = o.requests.get("https://www.investopedia.com/updates/penny-stocks-buy-technical-analysis/",headers=o.HEADERS,timeout=5).text #get the data
      d = r.split('displayed-date_1-0')[1].split("<")[0].split("Updated ")[1] # isolate the last updated date
      d = str(o.dt.datetime.strptime(d,"%b %d, %Y").date()) #convert from "mmm d, yyyy" to "yyyy-mm-dd"
      r = [e for e in r.split("<") if e.startswith("span")] #only use spans (other acronyms can appear in the paragraphs, and we don't want those)
      symbList = o.re.findall("\([A-Z]+\)", "".join(r)) #convert list back to string and pare down to wanted strings (the acronyms)
      symbList = {e[1:-1]:d+", techanal" for e in symbList} #trim off parens and convert to dict {symb:"date, type"}
      out.update(symbList) #append to output
      break
    except Exception:
      print("Error encoutered getting investopedia technical analysis penny stocks. Trying again...")
      if(verbose): print(f"{tries}/{maxTries}")
      tries+=1
      o.time.sleep(3)  
  
  
  #get the oil and gas penny stocks
  tries=0
  while tries<maxTries:
    try:
      r = o.requests.get("https://www.investopedia.com/investing/oil-gas-penny-stocks/",headers=o.HEADERS,timeout=5).text #get the data
      d = r.split('displayed-date_1-0')[1].split("<")[0].split("Updated ")[1] # isolate the last updated date
      d = str(o.dt.datetime.strptime(d,"%b %d, %Y").date()) #convert from "mmm d, yyyy" to "yyyy-mm-dd"
      rows = o.bs(r.replace("\n",""),'html.parser').find_all('tr') #remove newlines and get the rows
      rtx = [row.get_text() for row in rows] #remove all html data, just get text
      symbList = o.re.findall("\([A-Z.]+\)", "".join(rtx)) #get all data in the parens (should only be the symbols)
      symbList = {e[1:-1]:d+", oilgas" for e in symbList} #trim off parens and convert to dict {symb:"date, type"}
      out.update(symbList) #append to output
      break
    except Exception:
      print("Error encoutered getting investopedia oil and gas penny stocks. Trying again...")
      if(verbose): print(f"{tries}/{maxTries}")
      tries+=1
      o.time.sleep(3)  


  #get the technology penny stocks
  tries=0
  while tries<maxTries:
    try:
      r = o.requests.get("https://www.investopedia.com/investing/technology-penny-stocks/",headers=o.HEADERS,timeout=5).text #get the data
      d = r.split('displayed-date_1-0')[1].split("<")[0].split("Updated ")[1] # isolate the last updated date
      d = str(o.dt.datetime.strptime(d,"%b %d, %Y").date()) #convert from "mmm d, yyyy" to "yyyy-mm-dd"
      rows = o.bs(r.replace("\n",""),'html.parser').find_all('tr') #remove newlines and get the rows
      rtx = [row.get_text() for row in rows] #remove all html data, just get text
      symbList = o.re.findall("\([A-Z.]+\)", "".join(rtx)) #get all data in the parens (should only be the symbols)
      symbList = {e[1:-1]:d+", techno" for e in symbList} #trim off parens and convert to dict {symb:"date, type"}
      out.update(symbList) #append to output
      break
    except Exception:
      print("Error encoutered getting investopedia oil and gas penny stocks. Trying again...")
      if(verbose): print(f"{tries}/{maxTries}")
      tries+=1
      o.time.sleep(3)


  return out
    
  
#determine how much the take-profit should be for change since buy or change since close
def sellUp(symb=""):
  return float(c[algo]['sellUp'])

#determine how much the stop-loss should be for change since buy or change since close
def sellDn(symb=""):
  return float(c[algo]['sellDn'])


#get the stop loss for a symbol after its been triggered (default to the main value)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
