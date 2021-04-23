#This module should be any function that doesn't require alpaca or keys to use

import json,requests,os,time,re,csv,sys,configparser,threading
import datetime as dt
from bs4 import BeautifulSoup as bs
from math import ceil
from statistics import mean
from workdays import workday as wd

c = configparser.ConfigParser()
c.read('./configs/other.config')

stockDir = c['file locations']['stockDataDir'] #where stock history data is stored (csv files)
HEADERS = json.loads(c['net cfg']['headers']) #headers to send on each data request


#returns as 2d array order of Date, Close/Last, Volume, Open, High, Low sorted by dates newest to oldest (does not include today's info)
#get the history of a stock from the nasdaq api (date format is yyyy-mm-dd)
#default to returning the last year's worth of data
#TODO: possibly make a blank file for those that have failed as mark to show it's been tried but failed in the past?
def getHistory(symb, startDate=str(dt.date(dt.date.today().year-1,dt.date.today().month,dt.date.today().day)), endDate=str(dt.date.today()), maxTries=3,verbose=False):
  if(endDate<=startDate):
    raise Exception("Invalid Date Range (end<=start)")
  #try checking the modified date of the file, if it throws an error, just set it to yesterday
  try:
    modDate = dt.datetime.strptime(time.strftime("%Y-%m-%d",time.localtime(os.stat(stockDir+symb+'.csv').st_mtime)),"%Y-%m-%d").date() #if ANYONE knows of a better way to get the modified date into a date format, for the love of god please let me know
  except Exception:
    modDate = dt.date.today()-dt.timedelta(1)
  #write to file after checking that the file doesn't already exist (we don't want to abuse the api) or that it was edited more than a day ago
  if(not os.path.isfile(stockDir+symb+".csv") or modDate<dt.date.today()):
    
    tries=0 #set this to maxTries in the event that the old one dies (again)
    while tries<maxTries: #only try getting history with this method a few times before trying the next method
      tries += 1
      try:
        url = f'https://www.nasdaq.com/api/v1/historical/{symb}/stocks/{startDate}/{endDate}' #old api url (depreciated?)
        r = requests.get(url, headers=HEADERS, timeout=5).text #send request and store response
        if(len(r)<10):
          startDate = str(dt.datetime.strptime(startDate,"%Y-%m-%d").date()-dt.timedelta(1)) #try scooting back a day if at first we don't succeed (sometimes it returns nothing for some reason?)
        if('html' in r or len(r)<10): #sometimes response returns invalid data. This ensures that it's correct (not html error or blank data)
          raise ValueError('Returned invalid data') #sometimes the page will return html data that cannot be successfully parsed
        break
      except Exception:
        print(f"No connection, or other error encountered in getHistory for {symb}. Trying again...")
        time.sleep(3)
        continue
    
    with open(stockDir+symb+'.csv','w',newline='') as out: #write to file for later usage - old api used csv format
      if(tries>=maxTries):
        r = getHistory2(symb, startDate, endDate) #getHistory2 uses more requests and is more complex, so use it as a backup rather than a primary
        r = [['Date','Close/Last','Volume','Open','High','Low']]+r
        csv.writer(out,delimiter=',').writerows(r)
      else:
        out.write(r)
  
  else:
    if(verbose): print(f"{symb} file exists. Checking for proper data")
    with open(stockDir+symb+".csv",'r') as csv_file:
      csv_reader = csv.reader(csv_file, delimiter=',')
      lines = [[ee.replace('$','').replace('N/A','0').strip() for ee in e] for e in csv_reader][1::] #trim first line to get rid of headers, also replace $'s and N/A volumes to calculable values
      if(len(lines)==0): #if there's no data in the file, return nothing
        if(verbose): print("file contains invalid data")
        return []
    
    #get all the rows between the start and end dates
    rows = [e for e in lines if(startDate<=str(dt.datetime.strptime(e[0],"%m/%d/%Y").date())<=endDate)]
    sd = dt.datetime.strptime(startDate,"%Y-%m-%d").date()
    ed = dt.datetime.strptime(endDate,"%Y-%m-%d").date()

    # ensure that the startdate and enddate are workdays (startdate should look at the next workday, and enddate should look at the previous one as those should both be in range)
    sd = sd if sd.weekday()<=4 else wd(sd,1)
    ed = ed if ed.weekday()<=4 and ed<dt.date.today() else wd(ed,-1) #also need to ensure that enddate is not today
    
    if(len(rows)>0 and
       dt.datetime.strptime(rows[0][0],"%m/%d/%Y").date()==ed and
       dt.datetime.strptime(rows[-1][0],"%m/%d/%Y").date()==sd):
       if(verbose): print("file contains data")
       return rows
    
    else:
      if(verbose): print("file does not contain data. Repulling")
      #rm file and repull the data like the first part
      os.unlink(stockDir+symb+".csv")
      
      tries=0 #set this to maxTries in the event that the old one dies (again)
      while tries<maxTries: #only try getting history with this method a few times before trying the next method
        tries += 1
        try:
          url = f'https://www.nasdaq.com/api/v1/historical/{symb}/stocks/{startDate}/{endDate}' #old api url (depreciated?)
          r = requests.get(url, headers=HEADERS, timeout=5).text #send request and store response - cannot have empty user-agent
          if(len(r)<10):
            startDate = str(dt.datetime.strptime(startDate,"%Y-%m-%d").date()-dt.timedelta(1)) #try scooting back a day if at first we don't succeed (sometimes it returns nothing for some reason?)
          if('html' in r or len(r)<10): #sometimes response returns invalid data. This ensures that it's correct (not html error or blank data)
            raise ValueError('Returned invalid data') #sometimes the page will return html data that cannot be successfully parsed
          break
        except Exception:
          print(f"No connection, or other error encountered in getHistory for {symb}. Trying again...")
          time.sleep(3)
          continue
      
      with open(stockDir+symb+'.csv','w',newline='') as out: #write to file for later usage - old api used csv format
        if(tries>=maxTries):
          r = getHistory2(symb, startDate, endDate) #getHistory2 uses more requests and is more complex, so use it as a backup rather than a primary
          if(len(r)>0):
            r = [['Date','Close/Last','Volume','Open','High','Low']]+r
            csv.writer(out,delimiter=',').writerows(r)
          else:
            out.write(f"no data as of {dt.date.today()}")
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
#TODO: shouldn't be an issue for this case, but here's some logic:
#   if(todate-fromdate<22 and todate>1 month ago): 0-1 days will be returned
def getHistory2(symb, startDate, endDate, maxTries=3):
  if(endDate<=startDate):
    print("Invalid Date Data (end<=start)")
    return []
  
  maxDays = 5000 #max rows returned per request (~250 per year - so 5000=20 years max)
  tries=1
  j = {}
  while tries<=maxTries: #get the first set of dates
    try:
      j = json.loads(requests.get(f'https://api.nasdaq.com/api/quote/{symb}/historical?assetclass=stocks&fromdate={startDate}&todate={endDate}&limit={maxDays}',headers=HEADERS).text)
      break
    except Exception:
      print(f"Error in getHistory2 for {symb}. Trying again ({tries}/{maxTries})...")
      tries += 1
      time.sleep(3)
      pass
  
  if(tries>maxTries or j['data'] is None or j['data']['totalRecords']==0): #this could have a failure if the stock isn't found/returns nothing. More testing might be needed
    print(f"Failed to get {symb} history")
    return []
  else: #something's fucky with this api, jsyk
    if(j['data']['totalRecords']>maxDays): #get subsequent sets
      for i in range(1,ceil(j['data']['totalRecords']/(maxDays+1))):
        tries=1
        while tries<=maxTries:
          try:
            r = json.loads(requests.get(f'https://api.nasdaq.com/api/quote/{symb}/historical?assetclass=stocks&fromdate={startDate}&todate={endDate}&offset={i*(maxDays)}',headers=HEADERS).text)
            j['data']['tradesTable']['rows'] += r['data']['tradesTable']['rows'] #append the sets together
            break
          except Exception:
            print(f"Error in getHistory2 for {symb} index {i}. Trying again ({tries}/{maxTries})...")
            time.sleep(3)
            pass
          tries += 1
    
    #format the data to return the same as getHistory
    #2d array order of Date, Close/Last, Volume, Open, High, Low sorted by dates newest to oldest
    try:
      j = json.loads(json.dumps(j).replace('$','')) #remove $ characters
      out = [[e['date'],e['close'],e['volume'].replace(',',''),e['open'],e['high'],e['low']] for e in j['data']['tradesTable']['rows']]
    except Exception:
      out = []
      print("Failed to get history")
    return out

#return if the stock jumped today some %
def jumpedToday(symb,jump):
  url = f'https://api.nasdaq.com/api/quote/{symb}/summary?assetclass=stocks'
  tries=0
  maxTries = 3 #sometimes this one really hangs but it's not terribly important, so we set a max limit and just assume it didn't jump today if it fails
  while tries<maxTries:
    try:
      j = json.loads(requests.get(url,headers=HEADERS).text)
      close = float(j['data']['summaryData']['PreviousClose']['value'].replace('$','').replace(',','')) #previous day close
      high = float(j['data']['summaryData']['TodayHighLow']['value'].replace('$','').replace(',','').split('/')[0]) #today's high, today's low is index [1]
      #check that close & high are not "N/A" - sometimes the api returns no data, then check for the jump
      out = (close!="N/A" and high!="N/A") and (high/close>=jump)
      break
    except Exception:
      print(f"Error in jumpedToday. Trying again ({tries+1}/{maxTries} - {symb})...")
      time.sleep(3)
      out=False
      pass
    tries+=1
  return out


#get the ticker symbol and exchange of a company or return "-" if not found
def getSymb(company,maxTries=3):
  '''
  url = "https://www.nasdaq.com/search_api_autocomplete/search"
  tries=0
  while tries<maxTries:
    try:
      r = json.loads(requests.get(url,params={'q':company},headers=HEADERS,timeout=5).text)
      if(len(r[0]['value'].split(" "))>1): #this api also returns headlines which shouldn't count
        raise ValueError("Returned a hadline, not a symbol")
      [symb,exch] = [r[0]['value'],"NAS"]
      break
    except Exception:
      print(f"Error in getSymb of nasdaq api for '{company}'. Trying again...")
      tries+=1
      time.sleep(3)
      continue
  '''
  tries = maxTries+1 #bypassing the nasdaq one temporarily as it seems to not be as complete as the marketwatch one (it doesn't have as big of a database or is not as flexible at understanding what is being passed to it)
  
  #if the nasdaq api fails, then try falling back to the marketwatch one
  if(tries>=maxTries):
    # print(f"Failed nasdaq query for '{company}'. Trying marketwatch")
    url = "https://www.marketwatch.com/tools/quotes/lookup.asp" #this one is a bit slower than the nasdaq one, but may have more results. Use as a backup in case ythe nasdaq one fails
    tries=0
    while tries<maxTries: #get the html page with the symbol
      try:
        r = requests.get(url, params={"Lookup":company}, timeout=5).text
        break
      except Exception:
        print("No connection, or other error encountered in getSymb. Trying again...")
        tries+=1
        time.sleep(3)
        continue
    
    try: #parse throgh html to find the table, symbol data, symbol, and exchange for it
      table = bs(r,'html.parser').find_all('table')[0]
      symbData = table.find_all('tr')[1].find_all('td')
      symb = str(symbData[0]).split('">')[2].split("<")[0]
      exch = str(symbData[2]).split('">')[1].split("<")[0]
    except Exception: #return blanks if invalid
      [symb, exch] = ["-","-"]
  
  
  return [symb, exch]


#TODO: add slave functionality
#check if the master is alive
def masterLives():
  '''
  i=0
  while i<3: #try reaching the master 3 times
    try:
      r = requests.request(url = c[masterAddress])
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

#return stocks going through a reverse split (this list also includes ETFs)
def reverseSplitters():
  while True: #get page of upcoming stock splits
    try:
      r = json.loads(requests.get("https://api.nasdaq.com/api/calendar/splits", headers=HEADERS, timeout=5).text)['data']['rows']
      break
    except Exception:
      print("No connection, or other error encountered in reverseSplitters. trying again...")
      time.sleep(3)
      continue
  out = []
  for e in r:
    try: #normally the data is formatted as # : # as the ratio, but sometimes it's a %
      ratio = e['ratio'].split(" : ")
      ratio = float(ratio[0])/float(ratio[1])
    except Exception: #this is where it'd go if it were a %
      ratio = float(e['ratio'][:-1])/100+1 #trim the % symbol and convert to a number
    
    out.append([e['symbol'],ratio])
  
  
  return [e[0] for e in out if e[1]<1]
  

#get data that's in the info api call (current price returned by default)
# available data (at the moment): price, vol, mktcap, open, prevclose, istradable
#return dict of format {'option':value}
def getInfo(symb,data=['price']):
  url = f'https://api.nasdaq.com/api/quote/{symb}/info?assetclass=stocks' #use this URL to avoid alpaca
  while True:
    try:
      r = requests.get(url,headers={"User-Agent": "-"}, timeout=5).text #nasdaq url requires a non-empty user-agent string
      j = json.loads(r)
      break
    except Exception:
      print(f"No connection, or other error encountered in getInfo of {symb}. Trying again...")
      time.sleep(3)
      continue
  out = {}
  if('price' in data):
    try:
      out['price'] = float(j["data"]["primaryData"]["lastSalePrice"][1:])
    except Exception:
      out['price'] = 0
  if('vol' in data):
    try:
      out['vol'] = int(j['data']['keyStats']['Volume']['value'].replace(',',''))
    except Exception:
      out['vol'] = 0
  if('mktcap' in data):
    try:
      out['mktcap'] = int(j['data']['keyStats']['MarketCap']['value'].replace(',',''))
    except Exception:
      out['mktcap'] = 0
  if('open' in data):
    try:
      out['open'] = float(j['data']['keyStats']['OpenPrice']['value'][1:])
    except Exception:
      out['open'] = 0
  if('prevclose' in data):
    try:
      out['prevclose'] = float(j['data']['keyStats']['PreviousClose']['value'][1:])
    except Exception:
      out['prevclose'] = 0
  if('istradable' in data):
    try:
      out['istradable'] = (j['data']['exchange'].startswith('NYSE') or j['data']['exchange'].startswith('NASDAQ'))
    except Exception:
      out['istradable'] = False
  
  return out

#get minute to minute prices for the current day
def getDayMins(symb, maxTries=3, verbose=False):
  tries=0
  while tries<maxTries:
    try:
      r = json.loads(requests.get(f"https://api.nasdaq.com/api/quote/{symb}/chart?assetclass=stocks",headers=HEADERS).text)
      break
    except Exception:
      print(f"No connection or other error encountered in getDayMins. Trying again ({tries}/{maxTries})...")
      time.sleep(3)
      continue
  
  if(tries==maxTries):
    if(verbose): print("Failed to get minute data")
    return []
  else:
    out = {e['z']['dateTime']:float(e['z']['value']) for e in r['data']['chart']}
    return out
  
#get the next trade date in datetime date format
def nextTradeDate():
  while True:
    try:
      r = json.loads(requests.get("https://api.nasdaq.com/api/market-info",headers={"user-agent":'-'}).text)['data']['nextTradeDate']
      break
    except Exception:
      print("No connection or other error encountered in nextTradeDate. Trying again...")
      time.sleep(3)
      continue
  
  r = dt.datetime.strptime(r,"%b %d, %Y").date()
  
  return str(r)

#return dict of current prices of assets (symblist is list format of symb|assetclass) output of {symb|assetclass:{price,vol,open}}
def getPrices(symbList,maxTries=3):
  maxSymbs = 20 #cannot do more than 20 at a time, so loop through requests
  d = [] #init data var
  r = {}
  #loop through the symbols by breaking them into managable chunks for th api
  for i in range(0,len(symbList),maxSymbs):
    tries=0
    while tries<maxTries:
      try: #try getting the data
        r = json.loads(requests.get("https://api.nasdaq.com/api/quote/watchlist",params={'symbol':symbList[i:min(i+maxSymbs,len(symbList))]},headers=HEADERS,timeout=5).text)
        break
      except Exception: #if it doesn't work, try again
        print("Error getting prices. Trying again...")
        r['data'] = [] #if something fails, then set it to nothin in the event it completely fails out (this way it won't throw an error when trying to extend)
        tries+=1
        time.sleep(3)
        continue
    if(r['data'] is not None): d.extend(r['data']) #append the lists

  #isolate the symbols and prices and remove any that are none's
  prices = {f"{e['symbol']}|{e['assetClass']}":{
                                                'price':float(e['lastSalePrice'].replace("$","")),
                                                'vol':int(e['volume'].replace(",","")),
                                                'open':float(e['lastSalePrice'].replace("$",""))-(float(e['netChange']) if e['netChange']!='UNCH' else 0)
                                                } for e in d if(e['volume'] is not None and e['lastSalePrice'] is not None)}
  return prices
  

#get the time till the next market close in seconds (argument of EST offset (CST is 1 hour behind, UTC is 5 hours ahead))
def timeTillClose(estOffset=-1):
  while True:
    try:
      r = json.loads(requests.get("https://api.nasdaq.com/api/market-info",headers=HEADERS,timeout=5).text)
      ttc = r['data']['marketClosingTime'][:-3] #get the close time and strip off the timezone (" ET")
      ttc = dt.datetime.strptime(ttc,"%b %d, %Y %I:%M %p")+dt.timedelta(hours=estOffset)
      break
    except Exception:
      print("Error encountered in nasdaq timeTillClose. Trying again...")
      time.sleep(3)
      pass
  ttc = int((ttc-dt.datetime.now()).total_seconds())
  return ttc

#return the next market close time with an EST offset (required)
def closeTime(estOffset):
  while True:
    try:
      r = json.loads(requests.get("https://api.nasdaq.com/api/market-info",headers=HEADERS,timeout=5).text)
      close = r['data']['marketClosingTime'][:-3] #get the close time and strip off the timezone (" ET")
      close = dt.datetime.strptime(close,"%b %d, %Y %I:%M %p")+dt.timedelta(hours=estOffset)
      break
    except Exception:
      print("Error encountered in nasdaq closeTime. Trying again...")
      time.sleep(3)
      pass
  return close


#determine if the market is currently open or not
def marketIsOpen():
  while True:
    try:
      r = json.loads(requests.get("https://api.nasdaq.com/api/market-info",headers=HEADERS,timeout=5).text)
      isOpen = "Open" in r['data']['marketIndicator']
      break
    except Exception:
      print("Error encountered in nasdaq marketIsOpen. Trying again...")
      time.sleep(3)
      pass
  return isOpen

