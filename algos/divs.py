#this file contains functions specifically for the div algo
#what changes when a stock has a dividend?
#https://www.investopedia.com/articles/stocks/11/dividend-capture-strategy.asp

import ndaqfxns as n
import os,time,json,threading,configparser
import datetime as dt
from workdays import workday as wd

algo = os.path.basename(__file__).split('.')[0] #name of the algo based on the file name


def init(configFile,verbose=False):
  global c,posList

  if(verbose): print(f"reading config file {configFile}")
  #set the multi config file
  c = configparser.ConfigParser()
  c.read(configFile)
  
  #get the stocks held by this algo according to the records
  posListFile = c['file locations']['posList']
  if(verbose): print(f"reading posList file {posListFile}")
  lock = threading.Lock()
  lock.acquire()
  #read the whole file
  with open(posListFile,'r') as f:
    algoPos = json.loads(f.read())['algos']
    f.close()
  lock.release()
  if(algo in algoPos):
    if(verbose): print(f"{algo} is in posListFile with {len(algoPos[algo])} stocks")
    posList = algoPos[algo]
  else:
    if(verbose): print(f"{algo} not found in posList, init to empty")
    posList = {}

#return dict of {symb:note} where the note is payment date and div amount, formatted as "yyyy-mm-dd, $.$$"
def getList(verbose=True):
  #perform checks to see which one ones will gain
  #check history of the stocks. Look for pattern that denotes a gain after the initial div date (could possibly look like a buy low. Stock gains to div, div processes, dips, then gains again. Sell at that gain)
  
  #get the whole data lists for the specified dates (next trade date and the following day after that)
  
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()

  if(verbose):
    print(f"found {len(ul)} stocks to sort through for {algo}.")
    print(f"finding stocks for {algo}...")
  gb = goodBuys(ul)


  if(verbose): print(f"{len(gb)} found for {algo}.")
  return gb
  

#determine if a list of stocks are good to sell or not
#where symblist is a list of stocks and the function returns the same stocklist as a dict of {symb:goodsell(t/f)}
def goodSells(symbList, verbose=False):
  if(verbose): print("reading posListFile")
  lock = threading.Lock()
  lock.acquire()
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

  if(verbose): print("ensuring symbols in requested list are available in the posList")
  #make sure they're the ones in the posList only
  symbList = [e for e in symbList if e['symbol'] in posList]


  gs = {}
  for s in symbList:
    su = sellUp(s['symbol'])
    sd = sellDn(s['symbol'])
    
    daychng = float(s['change_today'])+1 #current price/last close price
    buychng = float(s['unrealized_plpc'])+1 #current price/buy price
    
  
    if(verbose):
      print(f"{s['symbol']}",
              f"open: {round(daychng,2)}", #change since open
              f"buy: {round(buychng,2)}", #change since buy
              f"sellUp: {su}",
              f"sellDn: {sd}")

    #check if price triggered up
    if(daychng>=su or buychng>=su):
      gs[s['symbol']] = 1
    #check if price triggered down
    elif(daychng<sd or buychng<sd):
      gs[s['symbol']] = -1
    else: #price didn't trigger either side
      gs[s['symbol']] = 0

  
  return gs

#get the whole json data (includes symb, dates, etc) based on the ex dates specified
#return dict of format {"symb":{date-data}}
def getUnsortedList(verbose=False):
  #get the next trade date as a date type
  ntt = n.nextTradeDate().date()
  #get the ex-div-dates for the next trade date, and the trade date after that (estimate as the next work day)
  exdatelist = [str(ntt),str(wd(ntt,1))]
  
  for exdate in exdatelist:
    if(verbose): print(f"getting dividends info for {exdate}")
    url = "https://api.nasdaq.com/api/calendar/dividends"
    params = {"date":exdate}
    r = None
    try:
      r = n.robreq(url=url,params=params,headers=n.HEADERS).json()
      r = r['data']['calendar']['rows']
    except Exception:
      print("bad data returned ")

    out = {}
    if(r is not None):
      if(verbose): print("converting output to dict")
      #change from a list to a dict of format {symb:data} and remove invalid dates (or ones that are N/A)
      for e in r:
        if(e['payment_Date']!="N/A"):
          out[e['symbol']] = e

    if(verbose): print(f"found {len(out)} stocks to sort through")
  
  return out

#get the latest div dates for a stock (announced, ex div, record, payment)
#this doesn't get used and is here for reference/future use
def getDivDates(symb,maxTries=3):
  tries = 0
  while tries<maxTries:
    try:
      #get the dividend info
      url = f"https://api.nasdaq.com/api/quote/{symb}/dividends?assetclass=stocks&limit=1"
      r = n.robreq(url=url,headers=n.HEADERS).json()
      r = r['data']['dividends']['rows'][0]
      break
    except Exception:
      print(f"Error in getting div dates for {symb}. Trying again...")
      tries+=1
      time.sleep(3)
      pass
  if(tries<maxTries):
    r = {}
    #TODO: there's probably a better way to do this than a bunch of try/excepts
    try:
      r['announcement'] = str(dt.datetime.strptime(r['declarationDate'],"%m/%d/%Y").date())
    except Exception:
      r['announcement'] = ''
    try:
      r['ex'] = str(dt.datetime.strptime(r['exOrEffDate'],"%m/%d/%Y").date())
    except Exception:
      r['ex'] = ''
    try:
      r['record'] = str(dt.datetime.strptime(r['recordDate'],"%m/%d/%Y").date())
    except Exception:
      r['record'] = ''
    try:
      r['payment'] = str(dt.datetime.strptime(r['paymentDate'],"%m/%d/%Y").date())
    except Exception:
      r['payment'] = ''
  else:
    print(f"Failed to get div dates for {symb}")
    r = {}
  return r


#where symbList is the output of getUnsortedList
#returns dict of stocks that are good to buy - format of {symb:note} where the note is formatted as "payoutDate, divAmt, divAmt/currentPrice"
def goodBuys(symbList, verbose=False):
  if(verbose): print(f"{len(symbList)} dividends found")

  #get the current price and volume
  if(verbose): print("checking prices and tradability")
  prices = n.getPrices([s+"|stocks" for s in symbList])
  if(verbose): print(f"{len(prices)} stocks available")
  
  if(verbose): print("setting configs")
  #min and max prices to keep things reasonable
  minPrice, maxPrice = float(c[algo]['minPrice']), float(c[algo]['maxPrice'])
  #minimum volume to allow liquidity
  minVol = float(c[algo]['minVol'])
  #minimum div amount (absolute dollars)
  minDiv = float(c[algo]['minDiv'])
  #minimum div/buyPrice to allow
  minDivYield = float(c[algo]['minDivYield'])
  #max time to allow for divs
  maxTime = float(c[algo]['maxTime'])
  #max symbols to allow to purchase per day
  maxSymbs = int(c[algo]['maxSymbs'])
  

  if(verbose): print("checking which stocks may be good to buy")
  gb={}
  for s in prices:
    symb = s.split('|')[0]
    price = prices[s]['price']
    vol = prices[s]['vol']
    #ensure price is within range and volume is sufficent
    #vol measures volume so far today which may run into issues if run during premarket or early in the day since the stock won't have much volume
    if(minPrice<=price<=maxPrice and vol>=minVol):
      if(verbose): print(f"{symb} is in price range with decent vol; ${price}; {vol}")
      #get the date that the payment should get disbursed
      pmtDate = dt.datetime.strptime(symbList[symb]['payment_Date'],"%m/%d/%Y").date()
      #actual div amount in $
      divRate = symbList[symb]['dividend_Rate']
      #div amount wrt price (approximate) in %
      divYield = divRate/price
      
      #mark as a good buy if pmt date is within a certain time, div rate is at least a certain amount, and div yield is at least a certain amount
      if((pmtDate-dt.date.today()).days<=maxTime and divRate>=minDiv and divYield>=minDivYield):
        if(verbose): print(f"{symb} is a good buy; div: ${divRate} ({round(divYield,3)}); days till pmt: {(pmtDate-dt.date.today()).days}")
        gb[symb] = f"{pmtDate}, {divRate}, {round(divYield,3)}"
      else:
        if(verbose): print(f"{symb} is not a good buy; div: ${divRate} ({round(divYield,3)}); days till pmt: {(pmtDate-dt.date.today()).days}")
    else:
      if(verbose): print(f"{symb} not in price range or vol is too low; ${price}; {vol}")
    
    if(verbose): print() #give some space for the output

  #if the stock list is too big, pare down to the specified max num by sorting by the biggest div yields
  if(len(gb)>maxSymbs):
    tmp = sorted([[symbList[s]['dividend_Rate']/prices[s+"|STOCKS"]['price'],s] for s in gb])[-maxSymbs:]
    for e in [e for e in gb if e not in [e[1] for e in tmp]]: gb.pop(e)
  
  return gb



#determine how much the take-profit should be for change since buy or change since close
def sellUp(symb="",verbose=False):
  lock = threading.Lock()
  lock.acquire()
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  [preSellUp, postSellUp] = [float(c[algo]['preSellUp']), float(c[algo]['postSellUp'])]

  if(symb in posList):
    today = dt.date.today()
    try:
      trigDate = dt.datetime.strptime(posList[symb]['note'].split(",")[0],"%Y-%m-%d").date()
    except Exception:
      trigDate = dt.date.today()
    
    if(today>=trigDate):
      #squeeze after the trigger date. Currently 1% per week, not set in the config
      postSellUp = max(1,postSellUp-(today-trigDate).days/7/100)
      return postSellUp
    else:
      return preSellUp
  else:
    if(verbose): print(f"{symb} not in posList of {algo}")
    return preSellUp

#determine how much the stop-loss should be for change since buy or change since close
#TODO: adjust sellDn % to be related to the yield % of the actual dividend (take bigger risks for bigger returns) - could also have it be related to volatility?
def sellDn(symb="",verbose=False):
  lock = threading.Lock()
  lock.acquire()
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  #get the sellDn values (before and after the trigger date)
  [preSellDn, postSellDn] = [float(c[algo]['preSellDn']), float(c[algo]['postSellDn'])]
  
  if(symb in posList and posList[symb]['sharesHeld']>0):
    today = dt.date.today()
    #attempt to grab the trigger date from the note, if it doesn't work, just set to today (better safe than sorry)
    try:
      trigDate = dt.datetime.strptime(posList[symb]['note'].split(",")[0],"%Y-%m-%d").date()
    except Exception:
      trigDate = dt.date.today()
    
    if(today>=trigDate):
      #squeeze after the trigger date. Currently 1% per week, not set in the config
      postSellDn = min(1,postSellDn+(today-trigDate).days/7/100)
      return postSellDn
    else:
      return preSellDn
  else:
    if(verbose): print(f"{symb} not in posList of {algo}")
    return preSellDn

#after triggering the take-profit, the price must fall this much before selling (trailing stop-loss % relative to max price since buy)
def sellUpDn():
  return float(c[algo]['sellUpDn'])
