#this file contains functions specifically for the double jump (aka dead cat bounce) algo
#when a penny stock gains a significant amount with a large volume then falls with a small volume, then it generally gains a second time

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

def init(configFile):
  global posList,c
  #set the multi config file
  #TODO: add error if the file doesn't exist.
  #TODO: in otherfxns, from configparser import ConfigParser (since I don't think we use anthing else)
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()

#get a list of potential gainers according to this algo
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  symbs = getUnsortedList()
  if(verbose): print(f"finding stocks for {algo}...")
  gb = goodBuys(symbs) #get dict of the list of stocks if they're good buys or not
  gb = {e:gb[e] for e in gb if gb[e][0].isnumeric()} #the only time that the first char is a number is if it is a valid/good buy
  if(verbose): print(f"{len(gb)} found for {algo}.")
  return gb

#TODO: add verbose-ness to goodBuys, goodSells

#checks whether something is a good buy or not (if not, return why - no initial jump or second jump already missed).
#if it is a good buy, return initial jump date
#this is where the magic really happens
#this function is depreciated, replaced by goodBuys
def goodBuy(symb,days2look = -1, verbose=False): #days2look=how far back to look for a jump
  if(days2look<0): days2look = int(c[algo]['simDays2look'])
  validBuy = "not tradable" #set to the jump date if it's valid
  if(o.getInfo(symb,['istradable'])['istradable']):
    #calc price % diff over past 20 days (current price/price of day n) - current must be >= 80% for any
    #calc volume % diff over average past some days (~60 days?) - must be sufficiently higher (~300% higher?)
    
    days2wait4fall = int(c[algo]['simWait4fall']) #wait for stock price to fall for this many days
    startDate = days2wait4fall + int(c[algo]['simStartDateDiff']) #add 1 to account for the jump day itself
    firstJumpAmt = float(c[algo]['simFirstJumpAmt']) #stock first must jump by this amount (1.3=130% over 1 day)
    sellUp = float(c[algo]['simSellUp']) #% to sell up at
    sellDn = float(c[algo]['simSellDn']) #% to sell dn at
    
    #make sure that the jump happened in the  frame rather than too long ago
    volAvgDays = int(c[algo]['simVolAvgDays']) #arbitrary number to avg volumes over
    checkPriceDays = int(c[algo]['simChkPriceDays']) #check if the price jumped suo.bstantially over the last __ trade days
    checkPriceAmt = float(c[algo]['simChkPriceAmt']) #check if the price jumped by this amount in the above days (% - i.e 1.5 = 150%)
    volGain = float(c[algo]['simVolGain']) #check if the volume increased by this amount during the jump (i.e. 3 = 300% or 3x, 0.5 = 50% or 0.5x)
    volLoss = float(c[algo]['simVolLoss']) #check if the volume decreases by this amount during the price drop
    priceDrop = float(c[algo]['simPriceDrop']) #price should drop this far when the volume drops
    
    start = str(o.dt.date.today()-o.dt.timedelta(days=(volAvgDays+days2look)))
    end = str(o.dt.date.today())
    
    dateData = o.getHistory(symb, start, end)
    
    if(startDate>=len(dateData)-2): #if a stock returns nothing or very few data pts
      validBuy = "Few data points available"
    else:
      validBuy = "initial jump not found"
      while(startDate<min(days2look, len(dateData)-2) and float(dateData[startDate][1])/float(dateData[startDate+1][1])<firstJumpAmt):
        startDate += 1
        
        #if the price has jumped sufficiently for the first time
        if(float(dateData[startDate][1])/float(dateData[startDate+1][1])>=firstJumpAmt):
          
          avgVol = sum([int(dateData[i][2]) for i in range(startDate,min(startDate+volAvgDays,len(dateData)))])/volAvgDays #avg of volumes over a few days
          
          lastVol = int(dateData[startDate][2]) #the latest volume
          lastPrice = float(dateData[startDate][4]) #the latest highest price
  
          if(lastVol/avgVol>volGain): #much larger than normal volume
            #volume had to have gained
            #if the next day's price has fallen significantly and the volume has also fallen
            if(float(dateData[startDate-days2wait4fall][4])/lastPrice-1<priceDrop and int(dateData[startDate-days2wait4fall][2])<=lastVol*volLoss):
              #the jump happened, the volume gained, the next day's price and volumes have fallen
              dayPrice = lastPrice
              i = 1 #increment through days looking for a jump - start with 1 day before startDate
              # check within the the last few days, check the price has risen compared to the past some days, and we're within the valid timeframe
              while(i<=checkPriceDays and lastPrice/dayPrice<checkPriceAmt and startDate+i<len(dateData)):
                dayPrice = float(dateData[startDate+i][4])
                i += 1
              
              if(lastPrice/dayPrice>=checkPriceAmt): #TODO: read through this logic some more to determine where exactly to put sellDn
                #the price jumped compared to both the previous day and to the past few days, the volume gained, and the price and the volume both fell
                #check to see if we missed the next jump (where we want to strike)
                missedJump = False
                validBuy = "Missed jump"
                if(not o.jumpedToday(symb, sellUp, maxTries=1)): #history grabs from previous day and before, it does not grab today's info. Check that it hasn't jumped today too (only query once since it's really not important)
                  for e in range(0,startDate):
                    if(verbose): print(str(dateData[e])+" - "+str(float(dateData[e][4])/float(dateData[e+1][1])) +" - "+ str(sellUp))
                    if(float(dateData[e][4])/float(dateData[e+1][1]) >= sellUp): #compare the high vs previous close
                      missedJump = True
                  if(not missedJump):
                    if(verbose): print(algo,symb)
                    validBuy = dateData[startDate][0] #return the date the stock initially jumped

  if(verbose): print(symb, validBuy)
  return validBuy
  

#perform the same checks as goodBuy but multiplexed for fewer requests
#returns a dict of {symb:validBuyText} where validBuyText will contain the failure reason or if it succeeds, then it is the initial jump date
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
  
  start = str(o.dt.date.today()-o.dt.timedelta(days=(volAvgDays+days2look)))
  end = str(o.dt.date.today())
  
  
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices of all valid stocks (invalid ones will not be returned by getPrices) - using as a filter to get rid of not tradable stocks
  symbList = [e.split("|")[0] for e in prices] #only look at the valid stocks
  
  out = {} #data to be returned
  
  for symb in symbList:
    startDate = days2wait4fall + int(c[algo]['simStartDateDiff']) #add 1 to account for the jump day itself

    dateData = o.getHistory(symb, start, end)
    if(startDate>=len(dateData)-2): #if a stock returns nothing or very few data pts
      validBuy = "Few data points available"
    else:
      validBuy = "initial jump not found"
      while(startDate<min(days2look, len(dateData)-2) and float(dateData[startDate][1])/float(dateData[startDate+1][1])<firstJumpAmt):
        startDate += 1
        
        #if the price has jumped sufficiently for the first time
        if(float(dateData[startDate][1])/float(dateData[startDate+1][1])>=firstJumpAmt):
          if(verbose): print(f"{symb}\tinitial price jumped on {dateData[startDate][0]}")
          avgVol = sum([int(dateData[i][2]) for i in range(startDate,min(startDate+volAvgDays,len(dateData)))])/volAvgDays #avg of volumes over a few days
          
          lastVol = int(dateData[startDate][2]) #the latest volume
          lastPrice = float(dateData[startDate][4]) #the latest highest price
  
          if(lastVol/avgVol>volGain): #much larger than normal volume
            if(verbose): print(f"{symb}\tvol gained")
            #volume had to have gained
            #if the next day's price has fallen significantly and the volume has also fallen
            if(float(dateData[startDate-days2wait4fall][4])/lastPrice-1<priceDrop and int(dateData[startDate-days2wait4fall][2])<=lastVol*volLoss):
              if(verbose): print(f"{symb}\tprice and vol dropped on {dateData[startDate-days2wait4fall][0]}")
              #the jump happened, the volume gained, the next day's price and volumes have fallen
              dayPrice = lastPrice
              i = 1 #increment through days looking for a jump - start with 1 day before startDate
              # check within the the last few days, check the price has risen compared to the past some days, and we're within the valid timeframe
              while(i<=checkPriceDays and lastPrice/dayPrice<checkPriceAmt and startDate+i<len(dateData)):
                dayPrice = float(dateData[startDate+i][4])
                i += 1
              
              if(lastPrice/dayPrice>=checkPriceAmt): #TODO: read through this logic some more to determine where exactly to put sellDn
                if(verbose): print(f"{symb}\t")
                #the price jumped compared to both the previous day and to the past few days, the volume gained, and the price and the volume both fell
                #check to see if we missed the next jump (where we want to strike)
                missedJump = False
                validBuy = "Missed jump"
                if(not o.jumpedToday(symb, sellUp, maxTries=1)): #history grabs from previous day and before, it does not grab today's info. Check that it hasn't jumped today too
                  for e in range(0,startDate):
                    if(verbose): print(str(dateData[e])+" - "+str(float(dateData[e][4])/float(dateData[e+1][1])) +" - "+ str(sellUp))
                    if(float(dateData[e][4])/float(dateData[e+1][1]) >= sellUp): #compare the high vs previous close
                      missedJump = True
                  if(not missedJump):
                    if(verbose): print(algo,symb)
                    validBuy = str(o.dt.datetime.strptime(dateData[startDate][0],"%m/%d/%Y").date()) #return the date the stock initially jumped (in yyyy-mm-dd format)
    
    if(verbose): print(symb+"\t"+validBuy)
    out[symb] = validBuy
    
  return out

#perform the same checks as goodSell but multiplexed for fewer requests
#return dict of {symb:goodSell}
def goodSells(symbList, verbose=False): #symbList is a list of stocks ready to be sold
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo] #load up the stock data for the algo
  lock.release()
  symbList = [e for e in symbList if e in posList] #only look at the stocks that are in the algo
  buyPrices = {s:float(posList[s]['buyPrice']) for s in symbList} #get buyPrices {symb:buyPrce}
  prices = o.getPrices([s+"|stocks" for s in symbList]) #currently format of {symb|assetclass:{price,vol,open}}
  prices = {s.split("|")[0]:prices[s] for s in prices} #now format of {symb:{price,vol,open}}
  
  gs = {}
  for s in symbList:
    if(s in prices):
      if(verbose): print(f"{s}\topen: {round(prices[s]['price']/prices[s]['open'],2)}\tbuy: {round(prices[s]['price']/buyPrices[s],2)}\tsellUp: {sellUp(s)}\tsellDn: {sellDn(s)}")
      #check if price triggered up
      if(prices[s]['price']/prices[s]['open']>=sellUp(s) or prices[s]['price']/buyPrices[s]>=sellUp(s)):
        gs[s] = 1
      #check if price triggered down
      elif(prices[s]['price']/prices[s]['open']<sellDn(s) or prices[s]['price']/buyPrices[s]<sellDn(s)):
        gs[s] = -1
      else: #price didn't trigger either side
        gs[s] = 0
    else:
      gs[s] = 0
  
  
  #display stocks that have an error
  for e in [e for e in symbList if e not in gs]:
    print(f"{e} not tradable")
  
  return gs


#get list of stocks from stocksUnder1 and marketWatch lists
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
  
  '''
  url = 'https://www.marketwatch.com/tools/stockresearch/screener/results.asp'
  #many of the options listed are optional and can be removed from the get request
  
  params = {
    "TradesShareEnable" : "True",
    "TradesShareMin" : str(c[algo]['simMinPrice']),
    "TradesShareMax" : str(c[algo]['simMaxPrice']),
    "PriceDirEnable" : "False",
    "PriceDir" : "Up",
    "LastYearEnable" : "False",
    "TradeVolEnable" : "true",
    "TradeVolMin" : str(c[algo]['simMinVol']),
    "TradeVolMax" : "",
    "BlockEnable" : "False",
    "PERatioEnable" : "False",
    "MktCapEnable" : "False",
    "MovAvgEnable" : "False",
    "MktIdxEnable" : "False",
    "Exchange" : "NASDAQ",
    "IndustryEnable" : "False",
    "Symbol" : "True",
    "CompanyName" : "False",
    "Price" : "False",
    "Change" : "False",
    "ChangePct" : "False",
    "Volume" : "False",
    "LastTradeTime" : "False",
    "FiftyTwoWeekHigh" : "False",
    "FiftyTwoWeekLow" : "False",
    "PERatio" : "False",
    "MarketCap" : "False",
    "MoreInfo" : "False",
    "SortyBy" : "Symbol",
    "SortDirection" : "Ascending",
    "ResultsPerPage" : "OneHundred"
  }
  
  params['PagingIndex'] = 0 #this will change to show us where in the list we should be - increment by 100 (see ResultsPerPage key)
  
  while True:
    try:
      r = o.requests.get(url, params=params, timeout=5).text
      totalStocks = int(r.split("matches")[0].split("floatleft results")[1].split("of ")[1]) #get the total number of stocks in the list - important because they're spread over multiple pages
      break
    except Exception:
      print("No connection or other error encountered in getList (MW). Trying again...")
      o.time.sleep(3)
      continue
  '''
      
  '''
  for i in range(0,totalStocks,100): #loop through the pages (100 because ResultsPerPage is OneHundred)
    if(verbose): print(f"page {int(i/100)+1} of {o.ceil(totalStocks/100)}")
    params['PagingIndex'] = i
    while True:
      try:
        r = o.requests.get(url, params=params, timeout=5).text
        break
      except Exception:
        print("No connection or other error encountered in getList (MW). Trying again...")
        o.time.sleep(3)
        continue

    try:
      table = o.bs(r,'html.parser').find_all('table')[0]
      for e in table.find_all('tr')[1::]:
        symbList.append(e.find_all('td')[0].get_text())
    except Exception:
      print("Error in MW website.")
  '''
  
  if(verbose): print("Getting MarketWatch data...")
  skip = 0
  resultsPerPage = 25 #new screener only returns 25 per page and can't be changed (afaict)
  pageList = [None] #init to some value so that its not empty
  while len(pageList)>0:
    pageList = [] #reinit once inside of the loop
    params['skip']=skip
    tries = 0
    while tries<maxTries:
      try:
        r = o.requests.get(url, params=params, timeout=5).text
        pageList = r.split('j-Symbol ">')[1:]
        pageList = [e.split(">")[1][:-3] for e in pageList]
        symbList += pageList
        if(verbose): print(f"MW page {int(skip/resultsPerPage)}")
        break
      except Exception:
        tries+=1
        print(f"Error getting MW data for {algo}. Trying again...")
        o.time.sleep(3)
        continue
    skip+=len(pageList)
  
  
  
  #now that we have the marketWatch list, let's get the stocksunder1 list - essentially the getPennies() fxn from other files
  if(verbose): print("Getting stocksunder1 data...")
  urlList = ['nasdaq','tech','biotech','marijuana','healthcare','energy'] #the ones not labeled for nasdaq are listed on OTC which we want to avoid
  for e in urlList:  
    if(verbose): print(e+" stock list")
    url = f'https://stocksunder1.org/{e}-penny-stocks/'
    tries=0
    while tries<maxTries:
      try:
        r = o.requests.post(url, params={"price":5,"volume":0,"updown":"up"}, timeout=5).text
        pageList = r.split('.php?symbol=')[1:]
        pageList = [e.split('">')[0] for e in pageList]
        symbList += pageList
        break
      except Exception:
        print("No connection, or other error encountered (SU1). Trying again...")
        o.time.sleep(3)
        tries+=1
        continue
    
  if(verbose): print("Removing Duplicates...")
  symbList = list(dict.fromkeys(symbList)) #combine and remove duplicates

  return symbList

#determine if a stock is a good sell or not
#depreciated, replaced with goodSells
def goodSell(symb):
  #check if price<sellDn
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  buyPrice = float(stockList[symb]['buyPrice'])
  inf = o.getInfo(symb,['price','open'])
  
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
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  mainSellUp = float(c[algo]['sellUp']) #account for squeeze here
  startSqueeze = float(c[algo]['startSqueeze'])
  squeezeTime = float(c[algo]['squeezeTime'])

  if(symb in stockList):
    try: #try setting the last jump, if it doesn't work, set it to yesterday TODO: this is logically wrong and should be fixed (something should change in the actual posList file)
      lastJump = o.dt.datetime.strptime(stockList[symb]['note'],"%Y-%m-%d").date()
    except Exception:
      lastJump = o.dt.date.today()-o.dt.timedelta(1)

    #after some weeks since the initial jump, the sell values should reach 1 after some more weeks
    #piecewise function: if less than time to start squeezing, remain constant, else start squeezing linearily per day
    sellUp = round(mainSellUp if(o.dt.date.today()<lastJump+o.dt.timedelta(startSqueeze*7)) else mainSellUp-(mainSellUp-1)*(o.dt.date.today()-(lastJump+o.dt.timedelta(startSqueeze*7))).days/(squeezeTime*7),2)
  else:
    sellUp = mainSellUp
  return sellUp

#get the sellDn value for a given symbol (default to the main value)
def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  stockList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  mainSellDn = float(c[algo]['sellDn'])
  startSqueeze = float(c[algo]['startSqueeze'])
  squeezeTime = float(c[algo]['squeezeTime'])
  
  if(symb in stockList):
    try: #try setting the last jump, if it doesn't work, set it to yesterday
      lastJump = o.dt.datetime.strptime(stockList[symb]['note'],"%Y-%m-%d").date()
    except Exception:
      lastJump = o.dt.date.today()-o.dt.timedelta(1)

    #after some weeks since the initial jump, the sell values should reach 1 after some more weeks
    #piecewise function: if less than time to start squeezing, remain constant, else start squeezing linearily per day
    sellDn = round(mainSellDn if(o.dt.date.today()<lastJump+o.dt.timedelta(startSqueeze*7)) else mainSellDn-(mainSellDn-1)*(o.dt.date.today()-(lastJump+o.dt.timedelta(startSqueeze*7))).days/(squeezeTime*7),2)

  else:
    sellDn = mainSellDn
  return sellDn

#get the stop loss for a symbol (default to the main value)
def sellUpDn(symb=""):
  mainSellUpDn = float(c[algo]['sellUpDn'])
  #if there's ever any future enhancement that we want to add here, we can
  return mainSellUpDn
