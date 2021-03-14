#this file contains functions specifically for the double jump algo
#when a penny stock gains a significant amount with a large volume then falls with a small volume, then it generally gains a second time
#dead cat bounce?

import otherfxns as o

algo = 'dj' #name of the algo
#stocks held by this algo
stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]


def getList():
  print(f"getting unsorted list for {algo}")
  symbs = getUnsortedList()
  print(f"finding stocks for {algo}")
  goodBuys = [e for e in symbs if goodBuy(e)[0].isnumeric()] #the only time that the first char is a number is if it is a valid/good buy
  print(f"{len(goodBuys)} found for {algo}")
  # print(goodBuys)
  return goodBuys


#checks whether something is a good buy or not (if not, return why - no initial jump or second jump already missed).
#if it is a good buy, return initial jump date
#this is where the magic really happens
def goodBuy(symb,days2look = int(o.c[algo]['simDays2look'])): #days2look=how far back to look for a jump
  validBuy = "NA" #set to the jump date if it's valid
  if o.isTradable(symb):
    #calc price % diff over past 20 days (current price/price of day n) - current must be >= 80% for any
    #calc volume % diff over average past some days (~60 days?) - must be sufficiently higher (~300% higher?)
    
    days2wait4fall = int(o.c[algo]['simWait4fall']) #wait for stock price to fall for this many days
    startDate = days2wait4fall + int(o.c[algo]['simStartDateDiff']) #add 1 to account for the jump day itself
    firstJumpAmt = float(o.c[algo]['simFirstJumpAmt']) #stock first must jump by this amount (1.3=130% over 1 day)
    sellUp = float(o.c[algo]['simSellUp']) #% to sell up at
    sellDn = float(o.c[algo]['simSellDn']) #% to sell dn at
    
    #make sure that the jump happened in the  frame rather than too long ago
    volAvgDays = int(o.c[algo]['simVolAvgDays']) #arbitrary number to avg volumes over
    checkPriceDays = int(o.c[algo]['simChkPriceDays']) #check if the price jumped suo.bstantially over the last __ trade days
    checkPriceAmt = float(o.c[algo]['simChkPriceAmt']) #check if the price jumped by this amount in the above days (% - i.e 1.5 = 150%)
    volGain = float(o.c[algo]['simVolGain']) #check if the volume increased by this amount during the jump (i.e. 3 = 300% or 3x, 0.5 = 50% or 0.5x)
    volLoss = float(o.c[algo]['simVolLoss']) #check if the volume decreases by this amount during the price drop
    priceDrop = float(o.c[algo]['simPriceDrop']) #price should drop this far when the volume drops
    
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
                if(not o.jumpedToday(symb, sellUp)): #history grao.bs from previous day and before, it does not grab today's info. Check that it hasn't jumped today too
                  for e in range(0,startDate):
                    # print(str(dateData[e])+" - "+str(float(dateData[e][4])/float(dateData[e+1][1])) +" - "+ str(sellUp))
                    if(float(dateData[e][4])/float(dateData[e+1][1]) >= sellUp): #compare the high vs previous close
                      missedJump = True
                  if(not missedJump):
                    print("dj",symb)
                    validBuy = dateData[startDate][0] #return the date the stock initially jumped
    
  return validBuy
  

  

#get list of stocks from stocksUnder1 and marketWatch lists
def getUnsortedList():
  symbList = list()
  
  url = 'https://www.marketwatch.com/tools/stockresearch/screener/results.asp'
  #many of the options listed are optional and can be removed from the get request
  params = {
    "TradesShareEnable" : "True",
    "TradesShareMin" : str(o.c[algo]['simMinPrice']),
    "TradesShareMax" : str(o.c[algo]['simMaxPrice']),
    "PriceDirEnable" : "False",
    "PriceDir" : "Up",
    "LastYearEnable" : "False",
    "TradeVolEnable" : "true",
    "TradeVolMin" : str(o.c[algo]['simMinVol']),
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
      
      
  print("Getting MarketWatch data...")
  for i in range(0,totalStocks,100): #loop through the pages (100 because ResultsPerPage is OneHundred)
    print(f"page {int(i/100)+1} of {o.ceil(totalStocks/100)}")
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
  
  #now that we have the marketWatch list, let's get the stocksunder1 list - essentially the getPennies() fxn from other files
  print("Getting stocksunder1 data...")
  urlList = ['nasdaq','tech','biotech','marijuana','healthcare','energy']
  for e in urlList:  
    print(e+" stock list")
    url = f'https://stocksunder1.org/{e}-penny-stocks/'
    while True:
      try:
        html = o.requests.post(url, params={"price":5,"volume":0,"updown":"up"}, timeout=5).content
        break
      except Exception:
        print("No connection, or other error encountered (SU1). Trying again...")
        o.time.sleep(3)
        continue
    table = o.bs(html,'html.parser').find_all('table')[6] #6th table in the webpage - this may change depending on the webpage
    for e in table.find_all('tr')[1::]: #skip the first element that's the header
      #print(o.re.sub(r'\W+','',e.find_all('td')[0].get_text().replace(' predictions','')))
      symbList.append(o.re.sub(r'\W+','',e.find_all('td')[0].get_text().replace(' predictions','')))
  
  
  print("Removing Duplicates...")
  symbList = list(dict.fromkeys(symbList)) #combine and remove duplicates
  
  print("Done getting stock lists")
  return symbList


#get the sellUp value for a given symbol
def sellUp(symb=""):
  mainSellUp = float(o.c[algo]['sellUp']) #account for squeeze here
  if(symb in stockList):
    try: #try setting the last jump, if it doesn't work, set it to yesterday TODO: this is logically wrong and should be fixed (something should change in the actual posList file)
      lastJump = o.dt.datetime.strptime(posList[algo][symb]['lastJumpDate'],"%Y-%m-%d").date()
    except Exception:
      lastJump = o.dt.date.today()-o.dt.timedelta(1)

    #sellUp change of 0 if <=5 weeks after initial jump, -.05 for every week after 6 weeks for a min of 1
    sellUp = round(max(1,mainSellUp-.05*max(0,int((o.dt.date.today()-(lastJump+o.dt.timedelta(6*7))).days/7))),2)

  else:
    sellUp = mainSellUp #account for squeeze here
  return sellUp




#get the sellDn value for a given symbol
def sellDn(symb=""):
  mainSellDn = float(o.c[algo]['sellDn'])
  if(symb in stockList):
    try: #try setting the last jump, if it doesn't work, set it to yesterday TODO: this is logically wrong and should be fixed (something should change in the actual posList file)
      lastJump = o.dt.datetime.strptime(stockList[symb]['lastJumpDate'],"%Y-%m-%d").date()
    except Exception:
      lastJump = o.dt.date.today()-o.dt.timedelta(1)

    #sellDn change of 0 if <=5 weeks after initial jump, +.05 for every week after 6 weeks for a max of 1
    sellDn = round(min(1,mainSellDn+.05*max(0,int((a.o.dt.date.today()-(lastJump+a.o.dt.timedelta(6*7))).days/7))),2)

  else:
    sellDn = mainSellDn #account for squeeze here
  return sellDn

def sellUpDn(symb=""):
  return float(o.c[algo]['sellUpDn'])