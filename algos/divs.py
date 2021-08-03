#this file contains functions specifically for the div algo
#what changes when a stock has a dividend?
#https://www.investopedia.com/articles/stocks/11/dividend-capture-strategy.asp

#TODO: incorporate preferential towards high yields (ag and more):
# https://www.investopedia.com/investing/agriculture-stocks-pay-dividends/

#TODO: adjust sellU/sellDn to be some function of price and dividend and date

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
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

#return dict of {symb:note} where the note is payment date and div amount, formatted as "yyyy-mm-dd, $.$$"
def getList(verbose=True):
  
  #perform checks to see which one ones will gain
  #check history of the stocks. Look for pattern that denotes a gain after the initial div date (could possibly look like a buy low. Stock gains to div, div processes, dips, then gains again. Sell at that gain)
  
  #if today < ex div date, then buy
  #TODO: have a minimum div amount? Or avg price to div amt?
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList(o.nextTradeDate()) #get the whole data list
  if(verbose): print(f"finding stocks for {algo}...")
  gb = goodBuys(ul)
  if(verbose): print(f"{len(gb)} found for {algo}.")
  return gb
  

#determine if a list of stocks are good to sell or not
#where symblist is a list of stocks and the function returns the same stocklist as a dict of {symb:goodsell(t/f)}
def goodSells(symbList, verbose=False):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  buyPrices = {e:posList[e]['buyPrice'] for e in posList} #get the prices each were bought at
  symbList = [e for e in symbList if e in posList] #make sure they're the ones in the posList only
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  gs = {}
  for s in symbList:
    if(s in prices):
      if(verbose): print(f"{s}\topen: {round(prices[s]['price']/prices[s]['open'],2)}\tbuy: {round(prices[s]['price']/buyPrices[s],2)}\tsellUp: {sellUp(s)}\tsellDn: {sellDn(s)}")
      #check if price triggered up
      if(prices[s]['open']>0 and buyPrices[s]>0):
        if(prices[s]['price']/prices[s]['open']>=sellUp(s) or prices[s]['price']/buyPrices[s]>=sellUp(s)):
          gs[s] = 1
        #check if price triggered down
        elif(prices[s]['price']/prices[s]['open']<sellDn(s) or prices[s]['price']/buyPrices[s]<sellDn(s)):
          gs[s] = -1
        else: #price didn't trigger either side
          gs[s] = 0
      else:
        gs[s] = 0
    else:
      gs[s] = 0
  
  
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


#where symbList is the output of getUnsortedList
#returns dict of stocks that are good to buy - format of {symb:note}
def goodBuys(symbList, verbose=False):
  if(verbose): print(f"{len(symbList)} dividends found")

  prices = o.getPrices([s+"|stocks" for s in symbList]) #get the current price and volume
  if(verbose): print(f"{len(prices)} stocks available")
  
  [minPrice,maxPrice] = [float(c[algo]['minPrice']),float(c[algo]['maxPrice'])] #min and max prices to keep things reasonable
  minVol = float(c[algo]['minVol']) #minimum volume to allow liquidity
  minDiv = float(c[algo]['minDiv']) #minimum div amount (absolute dollars). TODO May want to improve in the future to include div/share ratio
  maxTime = float(c[algo]['maxTime']) #max time to allow for divs
  
  gb={}
  for s in prices:
    if(minPrice<=prices[s]['price']<=maxPrice and prices[s]['vol']>=minVol):
      if(verbose): print(f"{s.split('|')[0]} is in price range with decent vol; ${prices[s]['price']}; {prices[s]['vol']}")
      pmtDate = o.dt.datetime.strptime(symbList[s.split("|")[0]]['payment_Date'],"%m/%d/%Y").date()
      divRate = symbList[s.split("|")[0]]['dividend_Rate']
      if((pmtDate-o.dt.date.today()).days<=maxTime and divRate>=minDiv):
        if(verbose): print(f"{s.split('|')[0]} is a good buy; div: ${divRate}; days till pmt: {(pmtDate-o.dt.date.today()).days}")
        gb[s.split("|")[0]] = str(pmtDate)+", "+str(divRate) #vol measures volume so far today which may run into issues if run during premarket or early in the day since the stock won't have much volume
      else:
        if(verbose): print(f"{s.split('|')[0]} is not a good buy; div: ${divRate}; days till pmt: {(pmtDate-o.dt.date.today()).days}")
    else:
      if(verbose): print(f"{s.split('|')[0]} not in price range or vol is too low; ${prices[s]['price']}; {prices[s]['vol']}")

  return gb



#determine how much the take-profit should be for change since buy or change since close
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  [preSellUp, postSellUp] = [float(c[algo]['preSellUp']), float(c[algo]['postSellUp'])]
  #TODO: account for note being blank or containing other text (just in case)

  if(symb in posList and str(o.dt.date.today())>=posList[symb]['note'].split(",")[0]):
    return postSellUp
  else:
    return preSellUp

#determine how much the stop-loss should be for change since buy or change since close
def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  [preSellDn, postSellDn] = [float(c[algo]['preSellDn']), float(c[algo]['postSellDn'])]
  
  if(symb in posList and str(o.dt.date.today())>=posList[symb]['note'].split(",")[0]):
    return postSellDn
  else:
    return preSellDn

#after triggering the take-profit, the price must fall this much before selling (rtailing stop-loss)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
