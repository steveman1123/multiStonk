#this file contains functions specifically for the double jump (aka dead cat bounce) algo
#when a penny stock gains a significant amount with a large volume then falls with a small volume, then it generally gains a second time

import ndaqfxns as n
import os,json,threading,time,configparser
import datetime as dt

algo = os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

#TODO: add error if the file doesn't exist.
#TODO: in otherfxns, from configparser import ConfigParser (since I don't think we use anthing else)
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

#get a list of potential gainers according to this algo
#return a 
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
  if(verbose): print(f"finding stocks for {algo}...")
  gb = goodBuys(ul) #get dict of the list of stocks if they're good buys or not
  gb = {e:gb[e] for e in gb if gb[e][0].isnumeric()} #the only time that the first char is a number is if it is a valid/good buy
  if(verbose): print(f"{len(gb)} found for {algo}.")
  return gb

#TODO: add verbose-ness to goodBuys

#checks whether something is a good buy or not (if not, return why - no initial jump or second jump already missed).
#if it is a good buy, return initial jump date
#this is where the magic really happens
#this function is depreciated, replaced by goodBuys
def goodBuy(symb,days2look = -1, verbose=False): #days2look=how far back to look for a jump
  if(days2look<0): days2look = int(c[algo]['simDays2look'])
  validBuy = "not tradable" #set to the jump date if it's valid
  if(n.getInfo(symb,['istradable'])['istradable']):
    #calc price % diff over past 20 days (current price/price of day n) - current must be >= 80% for any
    #calc volume % diff over average past some days (~60 days?) - must be sufficiently higher (~300% higher?)
    
    days2wait4fall = int(c[algo]['simWait4fall']) #wait for stock price to fall for this many days
    startDate = days2wait4fall + int(c[algo]['simStartDateDiff']) #add 1 to account for the jump day itself
    firstJumpAmt = float(c[algo]['simFirstJumpAmt']) #stock first must jump by this amount (1.3=130% over 1 day)
    sellUp = float(c[algo]['simSellUp']) #% to sell up at
    sellDn = float(c[algo]['simSellDn']) #% to sell dn at
    
    #make sure that the jump happened in the  frame rather than too long ago
    volAvgDays = int(c[algo]['simVolAvgDays']) #arbitrary number to avg volumes over
    checkPriceDays = int(c[algo]['simChkPriceDays']) #check if the price jumped substantially over the last __ trade days
    checkPriceAmt = float(c[algo]['simChkPriceAmt']) #check if the price jumped by this amount in the above days (% - i.e 1.5 = 150%)
    volGain = float(c[algo]['simVolGain']) #check if the volume increased by this amount during the jump (i.e. 3 = 300% or 3x, 0.5 = 50% or 0.5x)
    volLoss = float(c[algo]['simVolLoss']) #check if the volume decreases by this amount during the price drop
    priceDrop = float(c[algo]['simPriceDrop']) #price should drop this far when the volume drops
    
    start = str(dt.date.today()-dt.timedelta(days=(volAvgDays+days2look)))
    end = str(dt.date.today())
    
    dateData = n.getHistory(symb, start, end)
    dates = sorted(list(dateData),reverse=True)
    
    if(startDate>=len(dateData)-2): #if a stock returns nothing or very few data pts
      validBuy = "Few data points available"
    else:
      validBuy = "initial jump not found"
      while(startDate<min(days2look, len(dateData)-2) and dateData[dates[startDate]]['close']/dateData[dates[startDate+1]]['close']<firstJumpAmt):
        startDate += 1
        
        #if the price has jumped sufficiently for the first time
        if(dateData[dates[startDate]]['close']/dateData[dates[startDate+1]]['close']>=firstJumpAmt):
          
          avgVol = sum([dateData[dates[i]]['volume'] for i in range(startDate,min(startDate+volAvgDays,len(dateData)))])/volAvgDays #avg of volumes over a few days
          
          lastVol = dateData[dates[startDate]]['volume'] #the latest volume
          lastPrice = dateData[dates[startDate]]['high'] #the latest highest price
  
          if(lastVol/avgVol>volGain): #much larger than normal volume
            #volume had to have gained
            #if the next day's price has fallen significantly and the volume has also fallen
            if(dateData[dates[startDate-days2wait4fall]]['high']/lastPrice-1<priceDrop and dateData[dates[startDate-days2wait4fall]]['volume']<=lastVol*volLoss):
              #the jump happened, the volume gained, the next day's price and volumes have fallen
              dayPrice = lastPrice
              i = 1 #increment through days looking for a jump - start with 1 day before startDate
              # check within the the last few days, check the price has risen compared to the past some days, and we're within the valid timeframe
              while(i<=checkPriceDays and lastPrice/dayPrice<checkPriceAmt and startDate+i<len(dateData)):
                dayPrice = dateData[startDate+i]['high']
                i += 1
              
              if(lastPrice/dayPrice>=checkPriceAmt): #TODO: read through this logic some more to determine where exactly to put sellDn
                #the price jumped compared to both the previous day and to the past few days, the volume gained, and the price and the volume both fell
                #check to see if we missed the next jump (where we want to strike)
                missedJump = False
                validBuy = "Missed jump"
                if(not jumpedToday(symb, sellUp, maxTries=1)): #history grabs from previous day and before, it does not grab today's info. Check that it hasn't jumped today too (only query once since it's really not important)
                  for e in range(0,startDate):
                    #compare the high vs previous close
                    if(verbose): print(f"{dates[e]} - {dateData[dates[e]]['high']/dateData[dates[e+1]]['close']} - {sellUp}")
                    if(dateData[dates[e]]['high']/dateData[dates[e+1]]['close'] >= sellUp): 
                      missedJump = True
                  if(not missedJump):
                    if(verbose): print(algo,symb)
                    #return the date the stock initially jumped
                    validBuy = dates[startDate]

  if(verbose): print(symb, validBuy)
  return validBuy
  

#perform the same checks as goodBuy but multiplexed for fewer requests
#returns a dict of {symb:validBuyText} where validBuyText will contdjain the failure reason or if it succeeds, then it is the initial jump date
def goodBuys(symbList, days2look=-1, verbose=False):
  if(days2look<0): days2look = int(c[algo]['simDays2look'])
  #calc price % diff over past 20 days (current price/price of day n) - current must be >= 80% for any
  #calc volume % diff over average past some days (~60 days?) - must be sufficiently higher (~300% higher?)
  
  days2wait4fall = int(c[algo]['simWait4fall']) #wait for stock price to fall for this many days
  firstJumpAmt = float(c[algo]['simFirstJumpAmt']) #stock first must jump by this amount (1.3=130% over 1 day)
  sellUp = float(c[algo]['simSellUp']) #% to sell up at
  sellDn = float(c[algo]['simSellDn']) #% to sell dn at
  
  #make sure that the jump happened in the  frame rather than too long ago
  volAvgDays = int(c[algo]['simVolAvgDays']) #arbitrary number to avg volumes over
  checkPriceDays = int(c[algo]['simChkPriceDays']) #check if the price jumped substantially over the last __ trade days
  checkPriceAmt = float(c[algo]['simChkPriceAmt']) #check if the price jumped by this amount in the above days (% - i.e 1.5 = 150%)
  volGain = float(c[algo]['simVolGain']) #check if the volume increased by this amount during the jump (i.e. 3 = 300% or 3x, 0.5 = 50% or 0.5x)
  volLoss = float(c[algo]['simVolLoss']) #check if the volume decreases by this amount during the price drop
  priceDrop = float(c[algo]['simPriceDrop']) #price should drop this far when the volume drops
  
  start = str(dt.date.today()-dt.timedelta(days=(volAvgDays+days2look)))
  end = str(dt.date.today())
  
  if(verbose):
    print("days to wait for fall:",days2wait4fall)
    print("first jump amt:",firstJumpAmt)
    print("sellUp:",sellUp)
    print("sellDn:",sellDn)
    print("vol avg days:",volAvgDays)
    print("check price days:",checkPriceDays)
    print("check price amt:",checkPriceAmt)
    print("vol gain:", volGain)
    print("volLoss:",volLoss)
    print("price drop:",priceDrop)
    print("start date:",start)
    print("end date:",end)
    
  
  #get the vol, current and opening prices of all valid stocks (invalid ones will not be returned by getPrices) - using as a filter to get rid of not tradable stocks
  prices = n.getPrices([e+"|stocks" for e in symbList],maxTries=-1)['goodassets']
  symbList = [e.split("|")[0] for e in prices] #only look at the valid stocks
  
  if(verbose):
    print("\nsymb list:")
    print(symbList)
  
  out = {} #data to be returned
  
  for symb in symbList:
    startDate = days2wait4fall + int(c[algo]['simStartDateDiff']) #add 1 to account for the jump day itself
    
    #get the historical data (and reference dates sorted from newest to oldest)
    dateData = n.getHistory(symb, start, end)
    dates = sorted(list(dateData),reverse=True)
    
    if(startDate>=len(dateData)-2): #if a stock returns nothing or very few data pts
      validBuy = "Few data points available"
    else:
      validBuy = "initial jump not found"
      while(startDate<min(days2look, len(dateData)-2) and dateData[dates[startDate]]['close']/dateData[dates[startDate+1]]['close']<firstJumpAmt):
        startDate += 1
        
        #if the price has jumped sufficiently for the first time
        if(dateData[dates[startDate]]['close']/dateData[dates[startDate+1]]['close']>=firstJumpAmt):
          if(verbose): print(f"{symb}\tinitial price jumped on {dates[startDate]}")
          avgVol = sum([dateData[dates[i]]['volume'] for i in range(startDate,min(startDate+volAvgDays,len(dateData)))])/volAvgDays #avg of volumes over a few days
          
          #the latest volume
          lastVol = dateData[dates[startDate]]['volume']
          #the latest highest price
          lastPrice = dateData[dates[startDate]]['high']
  
          if(lastVol/avgVol>volGain): #much larger than normal volume
            if(verbose): print(f"{symb}\tvol gained")
            #volume had to have gained
            #if the next day's price has fallen significantly and the volume has also fallen
            if(dateData[dates[startDate-days2wait4fall]]['high']/lastPrice-1<priceDrop and dateData[dates[startDate-days2wait4fall]]['close']<=lastVol*volLoss):
              if(verbose): print(f"{symb}\tprice and vol dropped on {dates[startDate-days2wait4fall]}")
              #the jump happened, the volume gained, the next day's price and volumes have fallen
              dayPrice = lastPrice
              i = 1 #increment through days looking for a jump - start with 1 day before startDate
              # check within the the last few days, check the price has risen compared to the past some days, and we're within the valid timeframe
              while(i<=checkPriceDays and lastPrice/dayPrice<checkPriceAmt and startDate+i<len(dateData)):
                dayPrice = dateData[dates[startDate+i]]['high']
                i += 1
              
              if(lastPrice/dayPrice>=checkPriceAmt): #TODO: read through this logic some more to determine where exactly to put sellDn
                if(verbose): print(f"{symb}\t")
                #the price jumped compared to both the previous day and to the past few days, the volume gained, and the price and the volume both fell
                #check to see if we missed the next jump (where we want to strike)
                missedJump = False
                validBuy = "Missed jump"
                if(not jumpedToday(symb, sellUp)): #history grabs from previous day and before, it does not grab today's info. Check that it hasn't jumped today too
                  for e in range(0,startDate):
                    #compare the high vs previous close
                    if(verbose): print(f"{dateData[dates[e]]} - {round(dateData[dates[e]]['high']/dateData[dates[e+1]]['close'],2)} - {sellUp}")
                    if(dateData[dates[e]]['high']/dateData[dates[e+1]]['close'] >= sellUp):
                      missedJump = True
                  if(not missedJump):
                    if(verbose): print(algo,symb)
                    validBuy = dates[startDate] #return the date the stock initially jumped (in yyyy-mm-dd format)
    
    if(verbose): print(symb+"\t"+validBuy)
    out[symb] = validBuy
    
  return out

#return if the stock jumped today some %
def jumpedToday(symb,jump):
  j = n.getInfo(symb,data=['prevclose','hilo'])
  #check that close & high are not "N/A" - sometimes the api returns no data, then check for the jump
  out = (j['prevclose']>0 and j['high']>0) and (j['high']/j['prevclose']>=jump)
      
  return out


#perform the same checks as goodSell but multiplexed for fewer requests
#symbList = list of position objects from alpaca that are ready to be sold
#return dict of {symb:goodSell}
def goodSells(symbList, verbose=False):
  
  #read the currently held positions
  lock = threading.Lock()
  lock.acquire()
  #currently held positions of this algo
  posList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  
  #only get the objects of the symbs that are held in this algo
  #symblist is now alpaca position objects for stocks held in this algo
  symbList = [e for e in symbList if e['symbol'] in posList]
  
  #check that it has exceeded the stopLoss or takeProfit points
  gs = {}
  for s in symbList:
    su = sellUp(s['symbol'])
    sd = sellDn(s['symbol'])
    if(s['change_today']):
      daychng = float(s['change_today'])+1 #current price/last close price
    else:
      daychng = 1
    if(s['unrealized_plpc']):
      buychng = float(s['unrealized_plpc'])+1 #current price/buy price
    else:
      buychng = 1
    
    if(verbose):
      print(f"{s['symbol']}",
            f"daychng: {round(daychng,2)}", #change since open
            f"buychng: {round(buychng,2)}", #change since buy
            f"sellUp: {su}",
            f"sellDn: {sd}")

    #check if price triggered down
    if(daychng<sd or buychng<sd):
      gs[s['symbol']] = -1
    #check if price triggered up
    elif(daychng>=su or buychng>=su):
      gs[s['symbol']] = 1
    else: #price didn't trigger either side
      gs[s['symbol']] = 0

    if(verbose): print("gs?",gs[s['symbol']])
    
  #display stocks that have an error
  for e in [e for e in symbList if e['symbol'] not in gs]:
    print(f"{e['symbol']} not tradable in {algo}")
  
  return gs


#get list of stocks from stocksUnder1 and marketWatch lists
#TODO: should make this an otherfxns fxn with params so multiple algos can pull from the same code
def getUnsortedList(verbose=False, maxTries=3):
  symbList = list()
  url = "https://www.marketwatch.com/tools/screener/stock"
  
  params = {
    "exchange" : "nasdaq",
    "visiblecolumns" : "Symbol",
    "pricemin" : str(c[algo]['simMinPrice']),
    "pricemax" : str(c[algo]['simMaxPrice']),
    "volumemin" : str(c[algo]['simMinVol']),
    "partial" : "true"
  }
  
  if(verbose): print("Getting MarketWatch data...")
  skip = 0
  resultsPerPage = 25 #new screener only returns 25 per page and can't be changed (afaict)
  pageList = [None] #init to some value so that its not empty for the loop comparison
  while len(pageList)>0:
    pageList = [] #reinit once inside of the loop
    params['skip']=skip
    tries = 0
    while tries<maxTries:
      try:
        r = n.robreq(url, method="get", params=params,maxTries=1).text
        pageList = r.split('j-Symbol ">')[1:]
        pageList = [e.split(">")[1][:-3] for e in pageList]
        symbList += pageList
        if(verbose): print(f"MW page {int(skip/resultsPerPage)}")
        break
      except Exception:
        tries+=1
        print(f"Error getting MW data for {algo}. Trying again...")
        time.sleep(3)
        continue
    skip+=len(pageList)
  
  
  
  #now that we have the marketWatch list, let's get the stocksunder1 list - essentially the getPennies() fxn from other files
  if(verbose): print("Getting stocksunder1 data...")
  #TODO: ensure prices and volumes work for all types
  urlList = ['nasdaq']#,'tech','biotech','marijuana','healthcare','energy'] #the ones not labeled for nasdaq are listed on OTC which we want to avoid
  for e in urlList:  
    if(verbose): print(e+" stock list")
    url = f'https://stocksunder1.org/{e}-penny-stocks/'
    tries=0
    while tries<maxTries:
      try:
        r = n.robreq(url, method="post", params={"price":5,"volume":0,"updown":"up"}, maxTries=1).text
        pageList = r.split('.php?symbol=')[1:]
        pageList = [e.split('">')[0] for e in pageList]
        symbList += pageList
        break
      except Exception:
        print("No connection, or other error encountered (SU1). Trying again...")
        time.sleep(3)
        tries+=1
        continue
    
  if(verbose): print("Removing Duplicates...")
  symbList = list(dict.fromkeys(symbList)) #combine and remove duplicates

  return symbList


#determine if a stock is a good sell or not
#depreciated, replaced with goodSells
def goodSell(symb):
  #check if price<sellDn
  lock = threading.Lock()
  lock.acquire()
  stockList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  buyPrice = float(stockList[symb]['buyPrice'])
  inf = n.getInfo(symb,['price','open'])
  
  if(inf['open']>0):
    if(inf['price']/inf['open']<sellDn(symb) or inf['price']/inf['open']>=sellUp(symb)): #if change since open has gone beyond sell params
      return True
  else:
    print(f"{symb} open price is 0")
    return False
  
  if(buyPrice>0): #ensure buyPrice has been initiated/is valid
    if(inf['price']/buyPrice<sellDn(symb) or inf['price']/buyPrice>=sellUp(symb)): #if change since buy has gone beyond sell params
      return True
    elif(inf['price']/inf['open']<sellDn(symb) or inf['price']/inf['open']>=sellUp(symb)): #if change since open has gone beyond sell params
      return True
    else: #not enough change yet to consititute a sell
      return False
  else:
    return False

#get the sellUp value for a given symbol (default to the main value)
def sellUp(symb=""):
  lock = threading.Lock()
  lock.acquire()
  stockList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  mainSellUp = float(c[algo]['sellUp']) #account for squeeze here
  startSqueeze = float(c[algo]['startSqueeze'])
  squeezeTime = float(c[algo]['squeezeTime'])

  if(symb in stockList):
    try: #try setting the last jump, if it doesn't work, set it to yesterday TODO: this is logically wrong and should be fixed (something should change in the actual posList file)
      lastJump = dt.datetime.strptime(stockList[symb]['note'],"%Y-%m-%d").date()
    except Exception:
      lastJump = dt.date.today()-dt.timedelta(1)

    #after some weeks since the initial jump, the sell values should reach 1 after some more weeks
    #piecewise function: if less than time to start squeezing, remain constant, else start squeezing linearily per day until it reaches 1
    sellUp = round(mainSellUp if(dt.date.today()<lastJump+dt.timedelta(startSqueeze*7)) else max(mainSellUp-(mainSellUp-1)*(dt.date.today()-(lastJump+dt.timedelta(startSqueeze*7))).days/(squeezeTime*7),1),2)
  else:
    sellUp = mainSellUp
  return sellUp

#get the sellDn value for a given symbol (default to the main value)
def sellDn(symb=""):
  lock = threading.Lock()
  lock.acquire()
  stockList = json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  mainSellDn = float(c[algo]['sellDn'])
  startSqueeze = float(c[algo]['startSqueeze'])
  squeezeTime = float(c[algo]['squeezeTime'])
  
  if(symb in stockList):
    try: #try setting the last jump, if it doesn't work, set it to yesterday
      lastJump = dt.datetime.strptime(stockList[symb]['note'],"%Y-%m-%d").date()
    except Exception:
      lastJump = dt.date.today()-dt.timedelta(1)

    #after some weeks since the initial jump, the sell values should reach 1 after some more weeks
    #piecewise function: if less than time to start squeezing, remain constant, else start squeezing linearily per day until it reaches 1
    
    sellDn = round(mainSellDn if(dt.date.today()<lastJump+dt.timedelta(startSqueeze*7)) else min(mainSellDn-(mainSellDn-1)*(dt.date.today()-(lastJump+dt.timedelta(startSqueeze*7))).days/(squeezeTime*7),1),2)

  else:
    sellDn = mainSellDn
  return sellDn

#get the stop loss for a symbol (default to the main value)
def sellUpDn(symb=""):
  mainSellUpDn = float(c[algo]['sellUpDn'])
  #if there's ever any future enhancement that we want to add here, we can
  return mainSellUpDn
