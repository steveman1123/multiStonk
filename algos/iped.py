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
def getList(verbose=False):
  if(verbose): print("getting unsorted list...")
  ul = getUnsortedList()
  if(verbose): print("checking for goodBuys...")
  l = goodBuys(ul)
  if(verbose): print(l)
  out = {e:list(ul)[0] for e in l}
  return out
  
  
  

#multiplex the goodBuy fxn (symbList should be the output of getUnsortedList)
#return dict of {symb:t/f}
def goodBuys(symbList):
  
  #TODO: check prices and other info investopedia may have (plus cross reference with other sites)
  gb = {s:True for s in symbList[list(symbList)[0]]}
  return gb

#where symblist is a list of stocks and the function returns the same stocklist as a dict of {symb:goodsell(t/f)}
def goodSells(symbList):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  
  buyPrices = {e['buyPrice'] for e in posList}
  symbList = [e for e in symbList if e in posList] #make sure they're the ones in the posList only
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  gs = {e:(e not in prices or
           prices[e]['price']/prices[e]['open']>=sellUp(e) or
           prices[e]['price']/prices[e]['open']<sellDn(e) or
           prices[e]['price']/buyPrices[e]>=sellUp(e) or
           prices[e]['price']/buyPrices[e]<sellDn(e))
        for e in symbList} #return true if the price has reached a sellUp/dn point or it's not in the prices list
  
  return gs  

#get a list of stocks to be sifted through - returns dict of {date:[list, of, symbols]}
def getUnsortedList(verbose=False,maxTries=3):
  out = {}
  tries=0
  while tries<maxTries:
    try:
      r = o.requests.get("https://www.investopedia.com/updates/top-penny-stocks/",headers=o.HEADERS,timeout=5).text #get the data
      d = r.split('displayed-date_1-0')[1].split("<")[0].split("Updated ")[1] # isolate the last updated date
      d = str(o.dt.datetime.strptime(d,"%b %d, %Y").date()) #convert from "mmm d, yyyy" to "yyyy-mm-dd"
      
      r = [e for e in r.split("<") if e.startswith("span")] #only use spans (other acronyms can appear in the paragraphs, and we don't want those)
      symbList = o.re.findall("\([A-Z]+\)", "".join(r)) #convert list back to string and pare down to wanted strings (the acronyms)
      symbList = [e[1:-1] for e in symbList] #trim off parens
      out[d] = symbList
      break
    except Exception:
      print("Error encoutered getting investopedia stocks. Trying again...")
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
