#This module should be any function that doesn't require alpaca or keys to use
import json,requests,os,time,re,csv,configparser
import datetime as dt
from bs4 import BeautifulSoup as bs
from math import ceil

c = configparser.ConfigParser()
c.read('../common/common.config')

stockDir = c['File Locations']['stock data dir']


#check if a stock is listed on the market and is tradable
def isTradable(symb):
  isTradable = False
  while True:
    try:
      r = requests.request("GET","https://api.nasdaq.com/api/quote/{}/info?assetclass=stocks".format(symb), headers={"user-agent":"-"}, timeout=5).content
      break
    except Exception:
      print("No connection, or other error encountered in isTradable, trying again...")
      time.sleep(3)
      continue
  try:
    isTradable = bool(json.loads(r)['data']['isNasdaqListed'])
  except Exception:
    print(symb+" - Error in isTradable")

  return isTradable

#get list of stocks from stocksUnder1 and marketWatch lists
def getList(minPrice=0.8,maxPrice=5,minVol=300000):
  symbList = list()
  
  url = 'https://www.marketwatch.com/tools/stockresearch/screener/results.asp'
  #many of the options listed are optional and can be removed from the get request
  params = {
    "TradesShareEnable" : "True", 
    "TradesShareMin" : str(minPrice),
    "TradesShareMax" : str(maxPrice),
    "PriceDirEnable" : "False",
    "PriceDir" : "Up",
    "LastYearEnable" : "False",
    "TradeVolEnable" : "true",
    "TradeVolMin" : str(minVol),
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
      r = requests.get(url, params=params, timeout=5).text
      totalStocks = int(r.split("matches")[0].split("floatleft results")[1].split("of ")[1]) #get the total number of stocks in the list - important because they're spread over multiple pages
      break
    except Exception:
      print("No connection or other error encountered in getList (MW). Trying again...")
      time.sleep(3)
      continue
      
      
  print("Getting MarketWatch data...")
  for i in range(0,totalStocks,100): #loop through the pages (100 because ResultsPerPage is OneHundred)
    print(f"page {int(i/100)+1} of {ceil(totalStocks/100)}")
    params['PagingIndex'] = i
    while True:
      try:
        r = requests.get(url, params=params, timeout=5).text
        break
      except Exception:
        print("No connection or other error encountered in getList (MW). Trying again...")
        time.sleep(3)
        continue

    table = bs(r,'html.parser').find_all('table')[0]
    for e in table.find_all('tr')[1::]:
      symbList.append(e.find_all('td')[0].get_text())

  
  #now that we have the marketWatch list, let's get the stocksunder1 list - essentially the getPennies() fxn from other files
  print("Getting stocksunder1 data...")
  urlList = ['nasdaq','tech','biotech','marijuana','healthcare','energy']
  for e in urlList:  
    print(e+" stock list")
    url = 'https://stocksunder1.org/{}-penny-stocks/'.format(e)
    while True:
      try:
        html = requests.post(url, params={"price":5,"volume":0,"updown":"up"}, timeout=5).content
        break
      except Exception:
        print("No connection, or other error encountered (SU1). Trying again...")
        time.sleep(3)
        continue
    table = bs(html,'html.parser').find_all('table')[6] #6th table in the webpage - this may change depending on the webpage
    for e in table.find_all('tr')[1::]: #skip the first element that's the header
      #print(re.sub(r'\W+','',e.find_all('td')[0].get_text().replace(' predictions','')))
      symbList.append(re.sub(r'\W+','',e.find_all('td')[0].get_text().replace(' predictions','')))
  
  
  print("Removing Duplicates...")
  symbList = list(dict.fromkeys(symbList)) #combine and remove duplicates
  
  print("Done getting stock lists")
  return symbList


#returns as 2d array order of Date, Close/Last, Volume, Open, High, Low sorted by dates newest to oldest
#get the history of a stock from the nasdaq api (date format is yyyy-mm-dd)
def getHistory(symb, startDate, endDate, maxTries=10):
  #try checking the modified date of the file, if it throws an error, just set it to yesterday
  try:
    modDate = dt.datetime.strptime(time.strftime("%Y-%m-%d",time.localtime(os.stat(stockDir+symb+'.csv').st_mtime)),"%Y-%m-%d").date() #if ANYONE knows of a better way to get the modified date into a date format, for the love of god please let me know
  except Exception:
    modDate = dt.date.today()-dt.timedelta(1)
  #write to file after checking that the file doesn't already exist (we don't want to abuse the api) or that it was edited more than a day ago
  if(not os.path.isfile(stockDir+symb+".csv") or modDate<dt.date.today()):
    
    tries=0
    while tries<maxTries: #only try getting history with this method a few times before trying the next method
      try:
        url = f'https://www.nasdaq.com/api/v1/historical/{symb}/stocks/{startDate}/{endDate}' #old api url (depreciated?)
        r = requests.get(url, headers={"user-agent":"-"}, timeout=5).text #send request and store response - cannot have empty user-agent
        if(len(r)<10):
          startDate = str(dt.datetime.strptime(startDate,"%Y-%m-%d").date()-dt.timedelta(1)) #try scooting back a day if at first we don't succeed (sometimes it returns nothing for some reason?)
        if('html' in r or len(r)<10): #sometimes response returns invalid data. This ensures that it's correct (not html error or blank data)
          raise Exception('Returned invalid data') #sometimes the page will return html data that cannot be successfully parsed
        break
      except Exception:
        print("No connection, or other error encountered in getHistory. Trying again...")
        time.sleep(3)
        continue
      tries += 1
    
    with open(stockDir+symb+'.csv','w',newline='') as out: #write to file for later usage - old api used csv format
      if(tries>=maxTries):
        r = getHistory2(symb, startDate, endDate) #getHistory2 is slower/uses more requests, so not as good as getHistory, at least until we learn the api better
        r = [['Date','Close/Last','Volume','Open','High','Low']]+r
        csv.writer(out,delimiter=',').writerows(r)
      else:
        out.write(r)
  
  #read csv and convert to array
  #TODO: see if we can not have to save it to a file if possible due to high read/writes - can also eliminate csv library
  #     ^ or at least research where it should be saved to avoid writing to sdcard
  with open(stockDir+symb+".csv") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    out = [[ee.replace('$','').replace('N/A','0').strip() for ee in e] for e in csv_reader][1::] #trim first line to get rid of headers, also replace $'s and N/A volumes to calculable values
  
  return out

#use the new nasdaq api to return in the same format as getHistory
#this does NOT save the csv file
def getHistory2(symb, startDate, endDate, maxTries=10):
  maxDays = 14 #max rows returned per request
  tries=0
  while tries<maxTries: #get the first set of dates
    try:
      j = json.loads(requests.get(f'https://api.nasdaq.com/api/quote/{symb}/historical?assetclass=stocks&fromdate={startDate}&todate={endDate}',headers={'user-agent':'-'}).text)
      break
    except Exception:
      print("Error in getHistory2. Trying again...")
      time.sleep(3)
      continue
    tries += 1
  if(tries>=maxTries):
    print("Failed to get history 2")
    return []
  else:
    if(j['data']['totalRecords']>maxDays): #get subsequent sets
      for i in range(1,ceil(j['data']['totalRecords']/maxDays)):
        while True:
          try:
            r = json.loads(requests.get(f'https://api.nasdaq.com/api/quote/{symb}/historical?assetclass=stocks&fromdate={startDate}&todate={endDate}&offset={i*maxDays+i}',headers={'user-agent':'-'}).text)
            break
          except Exception:
            print("Error in getHistory2. Trying again...")
            time.sleep(3)
            continue
        j['data']['tradesTable']['rows'] += r['data']['tradesTable']['rows'] #append the sets together
    
    #format the data to return the same as getHistory
    #2d array order of Date, Close/Last, Volume, Open, High, Low sorted by dates newest to oldest
    out = [[e['date'],e['close'],e['volume'].replace(',',''),e['open'],e['high'],e['low']] for e in j['data']['tradesTable']['rows']]
    return out

#TODO: add slave functionality
#check if the master is alive
def masterLives():
  '''
  i=0
  while i<3: #try reaching the master 3 times
    try:
      r = requests.request(url=c['Master Slave']['masterAddress'])
      if(r is something good): #if it does reach the master and returns good signal
        return True
      else: #if it does reach the master but returns bad signal (computer is on, but script isn't running)
        break
    except Exception:
      i+=1
  return False
  '''
  
  #TODO: may have to install flask or something to get it online seperately from the web server
  print("No slave functionality yet")
  return True


#get the ticker symbol and exchange of a company or return "NA" if not found
def getSymb(company):
  url = f'http://app.quotemedia.com/quotetools/lookupSymbolsJson.go?jsoncallback=0&webmasterId=101264&searchString={company}'

  #url = "https://www.marketwatch.com/tools/quotes/lookup.asp" #this one is a little slow, it'd be nice to find a faster site
  while True: #get the html page with the symbol
    try:
      r = requests.get(url, timeout=5).text[2:-2]
      r = json.loads(r)['symbolLookup'][0]
      # r = requests.get(url, params={"Lookup":company}, timeout=5).text
      break
    except Exception:
      print("Connection Error. Trying again...")
      time.sleep(3)
      continue
  
  try: #parse throgh html to find the table, symbol data, symbol, and exchange for it
    [symb,exch] = [r['symbol'],r['exchange']]
    # table = bs(r,'html.parser').find_all('table')[0]
    # symbData = table.find_all('tr')[1].find_all('td')
    # symb = str(symbData[0]).split('">')[2].split("<")[0]
    # exch = str(symbData[2]).split('">')[1].split("<")[0]
  except Exception: #return blanks if invalid
    [symb, exch] = ["-","-"]
  return [symb, exch]
  
  
#use the nasdaq api to get time till open in seconds (only has accuracy to the nearest minute)
def timeTillOpen():
  while True:
    try:
      r = json.loads(requests.get('https://api.nasdaq.com/api/market-info',headers={'user-agent':'-'}).text)
      break
    except Exception:
      print("Connection error in timeTillOpen")
      continue
    
  cDn = r['data']['marketCountDown'].split(' ')[3:] #up to 1 minute off of actual time
  tto = int(cDn[0][:-1])*3600+int(cDn[1][:-1])*60 #parse the time into seconds
  return tto
  