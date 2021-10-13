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
  if(verbose): print(f"getting unsorted list for {algo}...")
  ntt = o.dt.datetime.strptime(o.nextTradeDate(),"%Y-%m-%d").date() #get the next trade date as a date type
  ul = getUnsortedList([str(ntt),str(o.wd(ntt,1))]) #get the whole data lists for the specified dates (next trade date and the following day after that
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
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

#get the whole json data (includes symb, dates, etc) based on the ex dates specified
def getUnsortedList(exdatelist, maxTries=3):
  out = {}
  
  for exdate in exdatelist:
    #print(exdate)
    tries=0
    r = None
    while tries<maxTries:
      try:
        #get the stocks whose exdivdate is the next trade date (buy before it drops to the dropped price)
        r = o.json.loads(o.requests.get(f"https://api.nasdaq.com/api/calendar/dividends?date={exdate}",headers={"user-agent":"-"}, timeout=5).text)['data']['calendar']['rows']
        break
      except Exception:
        print(f"Error in getting unsorted list for divs algo. Trying again ({tries}/{maxTries})...")
        tries+=1
        o.time.sleep(3)
        continue
    
    if(r is not None):
      #change from a list to a dict of format {symb:data} and remove invalid dates (or ones that are N/A)
      for e in r:
        if(e['payment_Date']!="N/A"):
          out[e['symbol']] = e
    #print(len(out))
  
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
#returns dict of stocks that are good to buy - format of {symb:note} where the note is formatted as "payoutDate, divAmt, divAmt/currentPrice"
def goodBuys(symbList, verbose=False):
  if(verbose): print(f"{len(symbList)} dividends found")

  prices = o.getPrices([s+"|stocks" for s in symbList]) #get the current price and volume
  if(verbose): print(f"{len(prices)} stocks available")
  
  [minPrice,maxPrice] = [float(c[algo]['minPrice']),float(c[algo]['maxPrice'])] #min and max prices to keep things reasonable
  minVol = float(c[algo]['minVol']) #minimum volume to allow liquidity
  minDiv = float(c[algo]['minDiv']) #minimum div amount (absolute dollars)
  minDivYield = float(c[algo]['minDivYield']) #minimum div/buyPrice to allow
  maxTime = float(c[algo]['maxTime']) #max time to allow for divs
  maxSymbs = int(c[algo]['maxSymbs']) #max symbols to allow to purchase per day
  
  gb={}
  for s in prices:
    if(minPrice<=prices[s]['price']<=maxPrice and prices[s]['vol']>=minVol):
      if(verbose): print(f"{s.split('|')[0]} is in price range with decent vol; ${prices[s]['price']}; {prices[s]['vol']}")
      pmtDate = o.dt.datetime.strptime(symbList[s.split("|")[0]]['payment_Date'],"%m/%d/%Y").date()
      divRate = symbList[s.split("|")[0]]['dividend_Rate']
      divYield = divRate/prices[s]['price']
      if((pmtDate-o.dt.date.today()).days<=maxTime and divRate>=minDiv and divYield>=minDivYield):
        if(verbose): print(f"{s.split('|')[0]} is a good buy; div: ${divRate}; days till pmt: {(pmtDate-o.dt.date.today()).days}")
        gb[s.split("|")[0]] = str(pmtDate)+", "+str(divRate)+", "+str(round(divYield,3)) #vol measures volume so far today which may run into issues if run during premarket or early in the day since the stock won't have much volume
      else:
        if(verbose): print(f"{s.split('|')[0]} is not a good buy; div: ${divRate}; days till pmt: {(pmtDate-o.dt.date.today()).days}")
    else:
      if(verbose): print(f"{s.split('|')[0]} not in price range or vol is too low; ${prices[s]['price']}; {prices[s]['vol']}")
  
  #if the stock list is too big, pare down to the specified max num by sorting by the biggest div yields
  if(len(gb)>maxSymbs):
    tmp = sorted([[symbList[s]['dividend_Rate']/prices[s+"|STOCKS"]['price'],s] for s in gb])[-maxSymbs:]
    for e in [e for e in gb if e not in [e[1] for e in tmp]]: gb.pop(e)
  
  return gb



#determine how much the take-profit should be for change since buy or change since close
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  [preSellUp, postSellUp] = [float(c[algo]['preSellUp']), float(c[algo]['postSellUp'])]
  #TODO: account for note being blank or containing other text (just in case)

  if(symb in posList):
    today = o.dt.date.today()
    try:
      trigDate = o.dt.datetime.strptime(posList[symb]['note'].split(",")[0],"%Y-%m-%d").date()
    except Exception:
      trigDate = o.dt.date.today()
    
    if(today>=trigDate):
      #squeeze after the trigger date. Currently 1% per week, not set in the config
      postSellUp = max(1,postSellUp-(today-trigDate).days/7/100)
      return postSellUp
    else:
      return preSellUp
  else:
    print(f"{symb} not in posList of {algo}")
    return preSellUp

#determine how much the stop-loss should be for change since buy or change since close
#TODO: adjust sellDn % to be related to the yield % of the actual dividend
def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  [preSellDn, postSellDn] = [float(c[algo]['preSellDn']), float(c[algo]['postSellDn'])]
  
  if(symb in posList and posList[symb]['sharesHeld']>0):
    today = o.dt.date.today()
    try:
      trigDate = o.dt.datetime.strptime(posList[symb]['note'].split(",")[0],"%Y-%m-%d").date()
    except Exception:
      trigDate = o.dt.date.today()
    
    if(today>=trigDate):
      #squeeze after the trigger date. Currently 1% per week, not set in the config
      postSellDn = min(1,postSellDn+(today-trigDate).days/7/100)
      return postSellDn
    else:
      return preSellDn
  else:
    print(f"{symb} not in posList of {algo}")
    return preSellDn

#after triggering the take-profit, the price must fall this much before selling (rtailing stop-loss)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
