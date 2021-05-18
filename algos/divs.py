#this file contains functions specifically for the div algo
#what changes when a stock has a dividend?
#https://www.investopedia.com/articles/stocks/11/dividend-capture-strategy.asp

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name


def init(configFile):
  global c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()

#return dict of {symb:note} where the note is payment date in yyyy-mm-dd format
def getList(verbose=True):
  
  #perform checks to see which one ones will gain
  #check history of the stocks. Look for pattern that denotes a gain after the initial div date (could possibly look like a buy low. Stock gains to div, div processes, dips, then gains again. Sell at that gain)
  
  #if today < ex div date, then buy

  if(verbose): print(f"getting unsorted list for {algo}...")
  data = getUnsortedList(o.nextTradeDate()) #get the whole data list
  if(verbose): print(f"finding stocks for {algo}...")
  prices = o.getPrices([s+"|stocks" for s in data]) #get the current price and volume
  goodBuys = {s.split("|")[0]:str(o.dt.datetime.strptime(data[s.split("|")[0]]['payment_Date'],"%m/%d/%Y").date()) for s in prices if float(c[algo]['minPrice'])<=prices[s]['price']<=float(c[algo]['maxPrice']) and prices[s]['vol']>=float(c[algo]['minVol'])} #vol measures volume so far today which may run into issues if run during premarket or early in the day since the stock won't have much volume
  if(verbose): print(f"{len(goodBuys)} found for {algo}.")
  return goodBuys
  

#return whether symb is a good sell or not
#if div is collected and price > buyPrice+div, then sell
#this function is now depreciated, replaced by goodSells
def goodSell(symb):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  
  dates = getDivDates(symb)
  if(symb not in posList):
    print(f"{symb} not found in {algo}")
    return True
  if(len(dates)>0): #make sure that the dates were populated
    curPrice = o.getInfo(symb)['price']
    if(curPrice/posList[symb]['buyPrice']<sellDn(symb)): #if change since buy has dropped below condition
      return True
    elif(str(o.dt.date.today())>dates['payment'] and
         curPrice/posList[symb]['buyPrice']>=sellUp(symb)): #if past the payment date and price has reached the sellUp point
      return True
    else:
      return False
  else:
    return False

#where symblist is a list of stocks and the function returns the same stocklist as a dict of {symb:goodsell(t/f)}
def goodSells(symbList):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  
  buyPrices = {e:posList[e]['buyPrice'] for e in posList} #get the prices each were bought at
  symbList = [e for e in symbList if e in posList] #make sure they're the ones in the posList only
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  #TODO: account for note being blank or containing other text
  #TODO: also add dividend amt to note (string format should be "yyyy-mm-dd, #.##")
  gs = {e:(e not in prices or
           (str(o.dt.date.today())>posList[e]['note'] and
            (prices[e]['price']/prices[e]['open']>=sellUp(e) or
             prices[e]['price']/prices[e]['open']<sellDn(e) or
             (buyPrices[e]>0 and
              prices[e]['price']/buyPrices[e]>=sellUp(e) or
              prices[e]['price']/buyPrices[e]<sellDn(e)
              )
             )
            )
           ) for e in symbList} #return true if the date is after the payment date and the price has reached a sellUp/dn point or it's not in the prices list
  
  return gs

#get the whole json data (includes symb, dates, etc) based on the ex date
def getUnsortedList(exdate):
  while True:
    try:
      #get the stocks whose exdivdate is the next trade date (buy before it drops to the dropped price)
      r = o.json.loads(o.requests.get(f"https://api.nasdaq.com/api/calendar/dividends?date={exdate}",headers={"user-agent":"-"}, timeout=5).text)['data']['calendar']['rows']
      break
    except Exception:
      print("Error in getting unsorted list for divs algo. Trying again...")
      o.time.sleep(3)
      pass
  out = {e['symbol']:e for e in r if(e['payment_Date']!="N/A")} #change from a list to a dict of format {symb:data} and remove invalid dates (or ones that are N/A)
  return out

#get the latest div dates for a stock (announced, ex div, record, payment)
def getDivDates(symb,maxTries=3):
  tries = 0
  while tries<maxTries:
    try:
      #
      r = o.json.loads(o.requests.get(f"https://api.nasdaq.com/api/quote/{symb}/dividends?assetclass=stocks&limit=1",headers={"user-agent":"-"}, timeout=5).text)['data']['dividends']['rows'][0]
      break
    except Exception:
      print(f"Error in getting div dates for {symb}. Trying again...")
      tries+=1
      o.time.sleep(3)
      pass
  if(tries<maxTries):
    r = {}
    #TODO: see if there can be some kind of error handling within strptim to catch, or use regex or something to ensure strings are in the right format
    try:
      r['announcement'] = str(o.dt.datetime.strptime(r['declarationDate'],"%m/%d/%Y").date())
    except Exception:
      r['announcement'] = ''
    try:
      r['ex'] = str(o.dt.datetime.strptime(r['exOrEffDate'],"%m/%d/%Y").date())
    except Exception:
      r['ex'] = ''
    try:
      r['record'] = str(o.dt.datetime.strptime(r['recordDate'],"%m/%d/%Y").date())
    except Exception:
      r['record'] = ''
    try:
      r['payment'] = str(o.dt.datetime.strptime(r['paymentDate'],"%m/%d/%Y").date())
    except Exception:
      r['payment'] = ''
    '''
    r = {
          'announcement':str(o.dt.datetime.strptime(r['declarationDate'] if r['declarationDate'],"%m/%d/%Y").date()),
          'ex':str(o.dt.datetime.strptime(r['exOrEffDate'],"%m/%d/%Y").date()),
          'record':str(o.dt.datetime.strptime(r['recordDate'],"%m/%d/%Y").date()),
          'payment':str(o.dt.datetime.strptime(r['paymentDate'],"%m/%d/%Y").date())
        }
    '''
  else:
    print(f"Failed to get div dates for {symb}")
    r = {}
  return r



#TODO: add comments
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  
  [preSellUp, postSellUp] = [float(c[algo]['preSellUp']), float(c[algo]['postSellUp'])]
  
  if(symb in posList and str(o.dt.date.today())>posList[symb]['note']):
    return postSellUp
  else:
    return preSellUp

def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())[algo]
  lock.release()
  
  [preSellDn, postSellDn] = [float(c[algo]['preSellDn']), float(c[algo]['postSellDn'])]
  
  if(symb in posList and str(o.dt.date.today())>posList[symb]['note']):
    return postSellDn
  else:
    return preSellDn

def sellUpDn():
  return float(c[algo]['sellUpDn'])
