#This module should be any function that doesn't require alpaca or keys to use

import json,requests,os,time,re,csv,sys,configparser
import datetime as dt
from bs4 import BeautifulSoup as bs
from math import ceil

c = configparser.ConfigParser()
c.read('./stonkbot.config')

stockDir = c['file locations']['stockDataDir']

#query nasdaq api to see if something is tradable on the market
def isTradable(symb):
  isTradable = False
  while True:
    try:
      r = json.loads(requests.request("GET",f"https://api.nasdaq.com/api/quote/{symb}/info?assetclass=stocks", headers={"user-agent":"-"}, timeout=5).content)
      break
    except Exception:
      print(f"No connection, or other error encountered in isTradable for {symb}, trying again...")
      time.sleep(3)
      continue
  if(r['data'] is not None):
    try:
      isTradable = bool(r['data']['isNasdaqListed'])
    except Exception:
      print(f"{symb} - Error in isTradable")

  return isTradable

#returns as 2d array order of Date, Close/Last, Volume, Open, High, Low sorted by dates newest to oldest (does not include today's info)
#get the history of a stock from the nasdaq api (date format is yyyy-mm-dd)
def getHistory(symb, startDate, endDate, maxTries=3):
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
        r = requests.get(url, headers={"user-agent":"-"}, timeout=5).text #send request and store response - cannot have empty user-agent
        if(len(r)<10):
          startDate = str(dt.datetime.strptime(startDate,"%Y-%m-%d").date()-dt.timedelta(1)) #try scooting back a day if at first we don't succeed (sometimes it returns nothing for some reason?)
        if('html' in r or len(r)<10): #sometimes response returns invalid data. This ensures that it's correct (not html error or blank data)
          raise Exception('Returned invalid data') #sometimes the page will return html data that cannot be successfully parsed
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
  maxDays = 14 #max rows returned per request
  tries=1
  j = {}
  while tries<=maxTries: #get the first set of dates
    try:
      j = json.loads(requests.get(f'https://api.nasdaq.com/api/quote/{symb}/historical?assetclass=stocks&fromdate={startDate}&todate={endDate}',headers={'user-agent':'-'}).text)
      break
    except Exception:
      print(f"Error in getHistory2 for {symb}. Trying again ({tries}/{maxTries})...")
      time.sleep(3)
      pass
    tries += 1
  if(j['data'] is None or tries>=maxTries or j['data']['totalRecords']==0): #TODO: this could have a failure if the stock isn't found/returns nothing
    print("Failed to get history")
    return []
  else: #something's fucky with this api, jsyk
    if(j['data']['totalRecords']>maxDays): #get subsequent sets
      for i in range(1,ceil(j['data']['totalRecords']/(maxDays+1))):
        tries=1
        while tries<=maxTries:
          try:
            r = json.loads(requests.get(f'https://api.nasdaq.com/api/quote/{symb}/historical?assetclass=stocks&fromdate={startDate}&todate={endDate}&offset={i*(maxDays+1)}',headers={'user-agent':'-'}).text)
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
      j = json.loads(requests.get(url,headers={'user-agent':'-'}).text)
      close = float(j['data']['summaryData']['PreviousClose']['value'].replace('$','').replace(',','')) #previous day close
      high = float(j['data']['summaryData']['TodayHighLow']['value'].replace('$','').replace(',','').split('/')[0]) #today's high, today's low is index [1]
      out = high/close>=jump
      break
    except Exception:
      print(f"Error in jumpedToday. Trying again ({tries+1}/{maxTries} - {symb})...")
      time.sleep(3)
      out=False
      pass
    tries+=1
  return out


#get the ticker symbol and exchange of a company or return "-" if not found
def getSymb(company):
  url = "https://www.marketwatch.com/tools/quotes/lookup.asp" #this one is a little slow, it'd be nice to find a faster site
  while True: #get the html page with the symbol
    try:
      r = requests.get(url, params={"Lookup":company}, timeout=5).text
      break
    except Exception:
      print("No connection, or other error encountered in getSymb. Trying again...")
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
      r = requests.request(url = c['masterAddress])
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
      r = json.loads(requests.get("https://api.nasdaq.com/api/calendar/splits", headers={"user-agent":"-"}, timeout=5).text)['data']['rows']
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
  
  


#set up the position list and do some error checking to make sure it's correct (take list of algos as arg in the event the pos list needs to be populated)
def setPosList(algoList):
  posList={}
  #if the posList file doesn't exist
  if(not os.path.isfile(c['file locations']['posList'])):
    with open(c['file locations']['posList'],'w') as f:
      f.write(json.dumps({e:{} for e in algoList}))
    posList = open(c['file locations']['posList'],'r').read()
  else: #if it does exist
    try: #try reading any json data from it
      #TODO: also check len() to make sure that all algos are present in the list? Might not have to, but will need to be tested
      with open(c['file locations']['posList'],'r') as f:
        posList = json.loads(f.read())
        if(len(posList)<len(algoList)):
          print("Adding missing algos to posList file")
          #TODO: the following loop could probably be replaced with a single line, something like: posList = {posList[e] for e in algoList if e in posList else algoList[e]}
          for algo in algoList:
            if(algo not in posList):
              posList[algo] = {}
    except Exception: #if it fails, then just write the empty algoList to the file
      #TODO: this is dangerous! This could potentially overwrite all saved position data if there's any error above. Make this more robust
      print("something went wrong. Overwriting file")
      with open(c['file locations']['posList'],'w') as f:
        f.write(json.dumps({e:{} for e in algoList}))
      posList = json.loads(open(c['file locations']['posList'],'r').read())

  return posList

