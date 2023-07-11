#This module should be any function that doesn't require alpaca or keys to use

#TODO: https://findwork.dev/blog/advanced-usage-python-requests-timeouts-retries-hooks/
#TODO: point all url tries/catches as a robreq() fxn like in multiforex

import json,requests,os,time,sys,configparser,threading,re

try:
  import Levenshtein as lev
except Exception:
  print("levenshtein is not installed. Working in degraded mode. Some errors may occur!")

import datetime as dt
import pytz
from bs4 import BeautifulSoup as bs
from statistics import mean
from workdays import workday as wd
from workdays import networkdays as nwd


#read the config file
configFile = "./configs/ndaq.config"
c = configparser.ConfigParser()
c.read(configFile)

#where stock history data is stored (json files)
stockDir = c['file locations']['stockDataDir']
#headers to send on each data request
HEADERS = json.loads(c['net cfg']['headers'])

BASEURL = "https://api.nasdaq.com/api"

#new york time zone (where the market is located)
nytz = pytz.timezone("US/Eastern")
#local timezone of the device running the script
localtz = pytz.timezone(time.tzname[1])



#robust request, standard request but simplified and made more robust
#return request object
def robreq(url,method="get",headers={},jsondata=None,params={},maxTries=3,timeout=5,verbose=False):
  tries=0
  while tries<maxTries or maxTries<0:
    if(verbose):
      print(f"requesting {url}")
      print("params:",params)
      print("headers:",headers)
      print("jsondata:",jsondata)

    try:
      r=requests.request(method,url,headers=headers,json=jsondata,params=params,timeout=timeout)
      if(r is not None and len(r.content)>0):
        return r
    except Exception:
      print(f"No connection or other error encountered for {url}")
      if(verbose):
        print("headers:",headers)
        print("params:",params)
      print(f"Trying again ({tries+1}/{maxTries})")
      tries+=1
      time.sleep(3)
  
  if(tries>=maxTries):
    print("url:",url)
    print("method:",method)
    print("headers:",headers)
    print("params:",params)
    raise ValueError("Could not get response") #TODO: have this return None instead of an error (need to make sure it doesn't break anything else because of this change)



#symb = stock ticker symbol (can also be other securities as long as assetclass is specified)
#startDate = string formatted as yyyy-mm-dd, must be before endData
#endDate = string formatted as yyyy-mm-dd, must be after startDate
#assetclass = type of security (can be one of: commodities|crypto|currencies|fixedincome|futures|index|mutualfunds|stocks)

#TODO: sometimes when this calls robreq and robreq has a connection problem, it'll just kick back no data instead of getting the actual data and performing as expected
'''
request logic is:
if(file exists):
  if(data in file):
    if(requested data fully contained in file):
      return saved data
    else:
      if(requested data is after stored data):
        request from end of data to today
      
      if(requested data is before stored data):
        request from beginnning of requested data to beginning of stored data using fromdate, offset, and limit
  else:
    request from start date to today
else:
    request from start date to today

trim ouput down to requested days  
'''

#returns a json object of format {date:{data},...}, writes to the data file
def getHistory(symb,startDate,endDate,assetclass="stocks",verbose=False):
  if(verbose): print(f"Getting history for {symb}")

  #ensure the start date and end date are in dt format
  if(type(startDate)==str):
    sdate = dt.datetime.strptime(startDate,"%Y-%m-%d").date()
  elif(type(startDate)==dt.date):
    sdate = startDate
  elif(type(startDate)==dt.datetime):
    sdate = startDate.date()
  else:
    raise ValueError("invalid start date type. Must be string formatted as yyyy-mm-dd, datetime.datetime, or datetime.date type")
  
  if(type(endDate)==str):
    edate = dt.datetime.strptime(endDate,"%Y-%m-%d").date()
  elif(type(endDate)==dt.date):
    edate = endDate
  elif(type(endDate)==dt.datetime):
    edate = endDate.date()
  else:
    raise ValueError("invalid end date type. Must be string formatted as yyyy-mm-dd, datetime.datetime, or datetime.date type")

  #if it's requesting today and the time is currently before market open), then set the end date to be either the friday before the weekend, or the day before (perform this before ensuring it's a week day, in the event that it's a monday morning)
  if(edate==dt.date.today() and dt.datetime.now().time()<dt.time(12,0)):
    if(verbose): print("requested end date is today, but it's still morning. setting to previous day")
    edate = dt.date.today()-dt.timedelta(days=1)
    
  #ensure the dates are on a week day
  if(dt.datetime.weekday(edate)>4):
    if(verbose): print(f"requested end date is a weekend ({edate}), setting to previous friday ({edate-dt.timedelta(days=dt.datetime.weekday(edate)-4)})")
    edate = edate-dt.timedelta(days=dt.datetime.weekday(edate)-4)
    
  if(dt.datetime.weekday(sdate)>4):
      if(verbose): print(f"requested start date is a weekend ({sdate}), setting to next monday ({sdate+dt.timedelta(days=7-dt.datetime.weekday(sdate))})")
      sdate = sdate+dt.timedelta(days=7-dt.datetime.weekday(sdate))
  
  
  if(edate<=sdate):
    raise ValueError(f"end date ({edate}) must be after start date ({sdate})")
  
  MINREQDAYS = 5 #a request for data must have at least this many days - anything less may return None and be invalid
  
  #set the place/file where to save the historical file
  #TODO: set this in the function call?
  saveFile = f"{stockDir}/{symb.upper()}.json"
  
  #set the api request url
  url = f"{BASEURL}/quote/{symb}/historical"
    
  #init the data
  #check if the file is present, if so, read it
  if(os.path.isfile(saveFile)):
    if(verbose): print(f"reading save file for {symb}")
    with open(saveFile,'r') as f:
      data = json.loads(f.read())
      f.close()
  else:
    if(verbose): print(f"saveFile {saveFile} does not exist. Initiating empty data")
    #init the data with info to be rewritten - use 9 and 0 because "9">"20xx-xx-xx" and "0"<"20xx-xx-xx" so will automatically be reset
    data={"hist":{},"meta":{'lastUpdated':str(dt.date.today()),'earliestRequested':"9",'latestRequested':"0"}}
    
  hist = data['hist']
  meta = data['meta']
  
  #if data is not present
  if(hist=={}):
    if(verbose): print("hist is empty")
    
    #set the requesting params
    params = {"fromdate":str((sdate-dt.timedelta(days=MINREQDAYS))),
              # "todate":str(edate),
              "limit":(dt.date.today()-sdate).days+MINREQDAYS,
              "assetclass":assetclass
             }
    if(verbose): print(f"attempting to request data for {symb} from {startDate} to {endDate}")
    #try requesting the data
    try:
      r = robreq(url=url,headers=HEADERS,params=params)
      #parse the data
      reqdata = json.loads(r.text)
      # print(json.dumps(data,indent=2))
      if(reqdata['data']['totalRecords']>0): #ensure data is present
        reqdata = reqdata['data']['tradesTable']['rows']
        #convert from list to dict (appending to any additional data already stored), convert numeric strings into just numerics (removing "$" and "," and converting missing info to 0)
        for e in reqdata:
          tmp = {}
          for f in e:
            if(f=="volume"): tmp[f] = int(e[f].replace(",","").replace("N/A","0"))
            elif(f!="date"): tmp[f] = float(e[f].replace("$","").replace("N/A","0"))
          
          hist[str(dt.datetime.strptime(e['date'],"%m/%d/%Y").date())] = tmp
          
      else: #no data points are available
        if(verbose): print("Total Records=0")
      
      data={"hist":hist,
            "meta":{
                    "lastUpdated":dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d-%H-%M"),
                    "earliestRequested":min(meta['earliestRequested'],str(sdate)),
                    "latestRequested":max(meta['latestRequested'],str(edate))}}
      #write the data to a file
      with open(saveFile,'w') as f:
        f.write(json.dumps(data))
        f.close()
      
    except Exception as e: #fail gracefully
      if(verbose):
        print(f"error getting historical data for {symb}")
        print(e)
      hist = {}

  
  else: #some data is present in the file, ensure that the requested data is present
    if(verbose): print(f"historical data is present ({len(hist)} rows)")
    
    #check metadata to see if there's historical data available before a given point
    if(meta['earliestRequested']<min(list(hist))):
      if(verbose): print("earliest request is before recorded history",meta['earliestRequested'],"<",min(list(hist)))
      if(str(edate)<min(list(hist))):
        if(verbose):print("end date is also before recorded history, no valid data to return",edate,"<",min(list(hist)))
        return {}
      
      if(str(sdate)<min(list(hist))):
        if(verbose): print("start date is also before recorded history, setting sdate to earliest available data",sdate,"<",min(list(hist)))
        sdate=dt.datetime.strptime(min(list(hist)),"%Y-%m-%d").date()
        
    
    #if requested start date is before the start of the recorded data
    if(str(sdate)<min(list(hist))):
      if(verbose): print("start date is before the start of recorded data",sdate,"<",min(list(hist)))
      
      #if the requested end date is either within or before the recorded data
      if(str(edate)<max(list(hist))):
        if(verbose): print("end date is either before or within the recorded data",edate,"<",max(list(hist)))
        #request all data from sdate to beginning of data
        
        #since the todate doesn't work past a certain point, use limit and offset to get the data between the sdate and start of recorded data
        #first request is just to get how many total records are present
        params = {"fromdate":str(sdate-dt.timedelta(days=MINREQDAYS)),
                  "limit":0
                 }
        try:
          r = robreq(url=url,headers=HEADERS,params=params)
          totalRecords = json.loads(r.text)['data']['totalRecords']
        except Exception as e:
          if(verbose):
            print(f"error getting total records for {symb}")
            print(e)
          totalRecords=0
        limit = (dt.datetime.strptime(min(list(hist)),"%Y-%m-%d").date()-sdate).days+MINREQDAYS
        offset = max(0,(dt.datetime.strptime(min(list(hist)),"%Y-%m-%d").date()-sdate).days+MINREQDAYS-limit)
        
        #second request is to
        
        #set the requesting params
        params = {"fromdate":str(sdate-dt.timedelta(days=MINREQDAYS)),
                  "limit":limit,
                  "offset":offset,
                  "assetclass":assetclass
                 }
        
        if(verbose): print(f"requesting {limit} data points starting from {params['fromdate']}")
        try:
          r = robreq(url=url,headers=HEADERS,params=params)
          #parse the data
          data = json.loads(r.text)
          if(data['data']['totalRecords']>0): #ensure data is present
            data = data['data']['tradesTable']['rows']
            #convert from list to dict (appending to any additional data already stored)
            for e in data:
              tmp = {}
              for f in e:
                if(f=="volume"): tmp[f] = int(e[f].replace(",","").replace("N/A","0"))
                elif(f!="date"): tmp[f] = float(e[f].replace("$","").replace("N/A","0"))
              
              hist[str(dt.datetime.strptime(e['date'],"%m/%d/%Y").date())] = tmp
          
          else: #no data points are available
            pass


          data={"hist":hist,
                "meta":{
                        "lastUpdated":dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d-%H-%M"),
                        "earliestRequested":min(meta['earliestRequested'],str(sdate)),
                        "latestRequested":max(meta['latestRequested'],str(edate))}}
          #write the data to a file
          with open(saveFile,'w') as f:
            f.write(json.dumps(data))
            f.close()

        except Exception: #fail gracefully
          if(verbose): print(f"error getting historical data for {symb}")
          hist = {}
        
      
      #if the requested end date is after the end of the recorded data
      else:
        if(verbose): print(f"end date is after the recorded data")
        #request all data from sdate to edate
        
        #set the requesting params
        params = { "fromdate":str((sdate-dt.timedelta(days=MINREQDAYS))),
                   "limit":(dt.date.today()-sdate).days+MINREQDAYS,
                   "assetclass":assetclass
                  }
        
        if(verbose): print(f"requesting data from {params['fromdate']} to today")
        try:
          r = robreq(url=url,headers=HEADERS,params=params)
          #parse the data
          data = json.loads(r.text)
          if(data['data']['totalRecords']>0): #ensure data is present
            data = data['data']['tradesTable']['rows']
            #convert from list to dict (appending to any additional data already stored)
            for e in data:
              tmp = {}
              for f in e:
                if(f=="volume"): tmp[f] = int(e[f].replace(",","").replace("N/A","0"))
                elif(f!="date"): tmp[f] = float(e[f].replace("$","").replace("N/A","0"))
              
              hist[str(dt.datetime.strptime(e['date'],"%m/%d/%Y").date())] = tmp
              
          else: #no data points are available
            pass
          
          data={"hist":hist,
                "meta":{
                        "lastUpdated":dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d-%H-%M"),
                        "earliestRequested":min(meta['earliestRequested'],str(sdate)),
                        "latestRequested":max(meta['latestRequested'],str(edate))}}

          #write the data to a file
          with open(saveFile,'w') as f:
            f.write(json.dumps(data))
            f.close()
      
        except Exception: #fail gracefully
          if(verbose): print(f"error getting historical data for {symb}")
          hist = {}
    
    #if the requested start date is within the data range
    elif(min(list(hist))<=str(sdate)<max(list(hist))):
      if(verbose): print(f"start date is within the recorded data range",min(list(hist)),"<=",sdate,"<",max(list(hist)))
      #if the end is also within the data range
      if(str(edate)<=max(list(hist))):
        if(verbose): print(f"end date is also within the recorded data range",edate,"<=",max(list(hist)))
        #isolate the data between the sdate and edate
        pass #the isolation occurs regardless after all this logic executes
        
      #end date is after the end of the recorded data
      else:
        if(verbose): print(f"end date is after the end of the recorded data",edate,">=",max(list(hist)))
        #request data from end of data to requested end date
        
        #set the requesting params
        params = { "fromdate":str((dt.datetime.strptime(max(list(hist)),"%Y-%m-%d")-dt.timedelta(days=MINREQDAYS)).date()),
                   "limit":(dt.date.today()-dt.datetime.strptime(max(list(hist)),"%Y-%m-%d").date()).days+MINREQDAYS,
                   "assetclass":assetclass
                  }
        
        if(verbose): print(f"requesting data from {params['fromdate']} to today")
        try:
          r = robreq(url=url,headers=HEADERS,params=params)
          #parse the data
          data = json.loads(r.text)
          if(data['data']['totalRecords']>0): #ensure data is present
            data = data['data']['tradesTable']['rows']
            #convert from list to dict (appending to any additional data already stored)
            for e in data:
              tmp = {}
              for f in e:
                if(f=="volume"): tmp[f] = int(e[f].replace(",","").replace("N/A","0"))
                elif(f!="date"): tmp[f] = float(e[f].replace("$","").replace("N/A","0"))
              
              hist[str(dt.datetime.strptime(e['date'],"%m/%d/%Y").date())] = tmp
        
          else: #no data points are available
            pass
        
          data={"hist":hist,
                "meta":{
                        "lastUpdated":dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d-%H-%M"),
                        "earliestRequested":min(meta['earliestRequested'],str(sdate)),
                        "latestRequested":max(meta['latestRequested'],str(edate))}}

          #write the data to a file
          with open(saveFile,'w') as f:
            f.write(json.dumps(data))
            f.close()
        
        except Exception: #fail gracefully
          if(verbose): print(f"error getting historical data for {symb}")
          hist = {}
    
    #requested start date is after the recorded data
    else:
      if(verbose): print(f"start date is after the recorded data")
      
      #request data from end of data to today
      
      #set the requesting params
      fromdate = dt.datetime.strptime(max(list(hist)),"%Y-%m-%d").date()
      limit = (dt.date.today()-fromdate).days+MINREQDAYS
      #adjust params to include the minimum required days
      params = {
                 "fromdate":str((fromdate-dt.timedelta(days=MINREQDAYS))),
                 "limit":limit,
                 "assetclass":assetclass
                }

      if(verbose): print(f"requesting data from {params['fromdate']} to today")
      try:
        r = robreq(url=url,headers=HEADERS,params=params)
        #parse the data
        data = json.loads(r.text)
        if(data['data']['totalRecords']>0): #ensure data is present
          data = data['data']['tradesTable']['rows']
          #convert from list to dict (appending to any additional data already stored)
          for e in data:
            tmp = {}
            for f in e:
              if(f=="volume"): tmp[f] = int(e[f].replace(",","").replace("N/A","0"))
              elif(f!="date"): tmp[f] = float(e[f].replace("$","").replace("N/A","0"))
            
            hist[str(dt.datetime.strptime(e['date'],"%m/%d/%Y").date())] = tmp
        
        else: #no data points are available
          pass

        data={"hist":hist,
              "meta":{
                      "lastUpdated":dt.datetime.strftime(dt.datetime.now(),"%Y-%m-%d-%H-%M"),
                      "earliestRequested":min(meta['earliestRequested'],str(sdate)),
                      "latestRequested":max(meta['latestRequested'],str(edate))}}

        #write the data to a file
        with open(saveFile,'w') as f:
          f.write(json.dumps(data))
          f.close()

      except Exception: #fail gracefully
        if(verbose): print(f"error getting historical data for {symb}")
        hist = {}

  
  #ensure it has the requested data
  if(hist!={}):
    #trim down the dict to the requested data
    hist = {e:hist[e] for e in list(hist) if sdate<=dt.datetime.strptime(e,"%Y-%m-%d").date()<=edate}
  else:
    if(verbose): print(f"could not get requested history for {symb}")
    
  return hist



#get the ticker symbol of a company or return None if not found
def getSymb(company,verbose=False):
  symb = ""
  
  #for now, just use the locally generated file
  if(os.path.isfile(c['file locations']['allSymbsFile'])):
    with open(c['file locations']['allSymbsFile'],'r') as f:
      symbList = json.loads(f.read())
      f.close()
  else:
    if(verbose): print("allSymbsFile not found. Generating new one")
    symbList = getAllSymbs()
  
  cname = "" #company name to compare to the query
  cnames = list(symbList) #list of symbols
  i = -1 #company name index of list() (init to -1 since it'll increment before checking the index)
  ratio = 0 #levenshtein ratio
  maxratio = 0 #max levenstein ratio seen
  ratiocutoff = 0.9 #cutoff to assume that it's a match
  #while the maxratio hasn't reached the cutoff
  while maxratio<ratiocutoff and i<len(cnames)-1:
    i+=1
    cname = symbList[cnames[i]]
    ratio = lev.ratio(company.lower(),cname.lower())
    maxratio = max(maxratio,ratio)
    if(verbose): print(company,cname,maxratio)
  
  symb = None #matched symbol
  if(maxratio>=ratiocutoff):
    symb = cnames[i]
  
  #idk where a good spot to find this info may be
  '''
  https://www.nasdaq.com/search_api_autocomplete/search?q=facebook
  https://stockmarketmba.com/symbollookupusingidentifier.php
  https://quotes.fidelity.com/mmnet/SymLookup.phtml?reqforlookup=REQUESTFORLOOKUP&productid=mmnet&isLoggedIn=mmnet&rows=50&for=stock&by=D&criteria=amazon&submit=Search
  and more I'm sure


  url = "https://www.nasdaq.com/search_api_autocomplete/search"
  params = {"q":company}
  r = json.loads(robreq(method="get",params=params,headers=HEADERS).text)[0]['value']


  url = "https://stocks.tradingcharts.com/stocks/symbols/s/us/{company}"
  r = robreq(url=url,headers=HEADERS).text
  r = r.split("<tr>")[1:-1]
  r = [e.split("rowspan=1>") for e in r]
  print(r)
  '''
  
  
  
  return symb


#get all nasdaq symbols and company names into a json object and save to a json file
#format of {"symb":"company name"}
def getAllSymbs(verbose=False):
  cs = {}

  for i in range(65,91): #ASCII A-Z
    if(verbose): print(chr(i),end=" - ",flush=True)
    r = requests.get(f"http://www.advfn.com/nasdaq/nasdaq.asp?companies={chr(i)}",headers={"User-Agent":'test/1.0'},timeout=500).text

    table = r.split("Info</th>")[1].split("</table")[0]
    s = BeautifulSoup(table, features="html.parser")


    for r in s.find_all('tr'):
      o = []
      for d in r.find_all('td'):
        o.append(d.get_text())
      cs[o[1]] = o[0]

    if(verbose): print(f"total: {len(cs)}")

  if(verbose): print(len(cs))
  with open(c['file locations']['allSymbsFile'],'w') as f:
    f.write(json.dumps(cs))
    f.close()
  return cs



#return stocks going through a reverse split (this list also includes ETFs)
def reverseSplitters():
  tries=0
  try:
    r=json.loads(robreq(url=url,headers=HEADERS).text)
  except Exception:
    r={}
  
  out = []
  if('data' in r and r['data'] is not None and 'rows' in r['data']):
    r = r['data']['rows']
  else:
    return out
  for e in r:
    try: #normally the data is formatted as # : # as the ratio, but sometimes it's a %
      ratio = e['ratio'].split(" : ")
      ratio = float(ratio[0])/float(ratio[1])
    except Exception: #this is where it'd go if it were a %
      ratio = float(e['ratio'][:-1])/100+1 #trim the % symbol and convert to a number
    
    out.append([e['symbol'],ratio])
  
  
  return [e[0] for e in out if e[1]<1]
  

#get data that's in the info api call (current price returned by default)
# available data (at the moment): ['price', 'vol', 'mktcap', 'open', 'prevclose', 'istradable','hilo']
#return dict of format {'option':value}
#TODO: on err of something not present, set to None rather than 0
def getInfo(symb,data=['price'], verbose=False):
  data = [e.lower() for e in data]
  if(verbose): print("request data:",data)
  
  #use these URLs to avoid alpaca
  infurl = f'{BASEURL}/quote/{symb}/info?assetclass=stocks'
  sumurl = f'{BASEURL}/quote/{symb}/summary?assetclass=stocks'
  infj = json.loads(robreq(url=infurl,headers=HEADERS,timeout=5).text)
  sumj = json.loads(robreq(url=sumurl,headers=HEADERS,timeout=5).text)


  out = {} #init the output variable
  #determine which data to output in the request
  if('price' in data):
    try:
      out['price'] = float(infj["data"]["primaryData"]["lastSalePrice"][1:])
    except Exception:
      out['price'] = 0
  if('vol' in data):
    try:
      out['vol'] = int(sumj['data']['summaryData']['ShareVolume']['value'].replace(',',''))
    except Exception:
      out['vol'] = 0
  if('mktcap' in data): #moved to summary
    try:
      out['mktcap'] = int(sumj['data']['summaryData']['MarketCap']['value'].replace(',',''))
    except Exception:
      out['mktcap'] = 0
  if('open' in data):
    try:
      out['open'] = float(infj['data']['primaryData']['lastSalePrice'][1:])+float(infj['data']['primartData']['netchange'])
    except Exception:
      out['open'] = 0
  if('prevclose' in data):
    try:
      out['prevclose'] = float(sumj['data']['summaryData']['PreviousClose']['value'][1:])
    except Exception:
      out['prevclose'] = 0
  if('istradable' in data):
    try:
      out['istradable'] = (infj['data']['exchange'].startswith('NYSE') or infj['data']['exchange'].startswith('NASDAQ'))
    except Exception:
      out['istradable'] = False
  if('hilo' in data):
    try:
      hilo = sumj['data']['summaryData']['TodayHighLow'].split("/")
      out['high'] = float(hilo[0][1:])
      out['low'] = float(hilo[1][1:])
    except Exception:
      out['high'] = 0
      out['low'] = 0
  
  if(verbose): print("returned data:",list(out))
  return out


#get day chart prices for the current day (not exactly minute to minute)
def getChart(symb, verbose=False):
  r = json.loads(robreq(f"{BASEURL}/quote/{symb}/chart?assetclass=stocks",headers=HEADERS).text)
  
  out = {e['z']['dateTime']:float(e['z']['value']) for e in r['data']['chart']}
  return out


#get the next trade date in datetime date format
def nextTradeDate(verbose=False):
  try:
    r = json.loads(robreq(url=f"{BASEURL}/market-info",headers=HEADERS).text)
    r = dt.datetime.strptime(r['data']['nextTradeDate'],"%b %d, %Y")
    # r = dt.datetime.strptime(r['data']['nextTradeDate'],"%Y-%m-%d")
    return r
  except Exception:
    if(verbose): print("error getting data. Assuming next workday")
    return wd(dt.date.today(),1)
  

#return dict of current prices of assets
#symblist = list format of symb|assetclass
#maxTries = number of tries to attempt to connect to api
#verbose = verbosity
#output dict {"symb|assetclass":{price,vol,open}}
#TODO: this function returns errors fairly often (especially in the api endpoint and periodically that the data returned doesn't have anything in it)
def getPrices(symbList,maxTries=3,verbose=False):
  #ensure there are no spaces in the query
  #TODO: should check for other illegal characters using regex
  symbList = [e.replace(" ","") for e in symbList]

  maxSymbs = 20 #cannot do more than 20 at a time, so loop through requests
  d = [] #init data var
  r = {} #init request var
  #loop through the symbols by breaking them into managable chunks for the api
  for i in range(0,len(symbList),maxSymbs):
    if(verbose): print(f"get prices ({i}-{min(i+maxSymbs,len(symbList))}/{len(symbList)})")
    symbQuery = symbList[i:min(i+maxSymbs,len(symbList))]
    r = robreq(f"{BASEURL}/quote/watchlist",params={'symbol':symbQuery},maxTries=maxTries,headers=HEADERS,timeout=5,verbose=False).json()

    if(verbose): print(r)

    #if the list has data, append it
    if(r['data'] is not None):
      if(verbose): print(len(r['data']))
      d.extend(r['data']) #append the lists
    else: #else if there's no data, don't append the list and let us know
      print(f"Error getting prices")

  #isolate the symbols and prices and remove any that are none's
  prices={}
  for e in d: #for every symb in the data
    #ensure that all data is present and valid
    if(e['volume'] is not None and len(e['volume'])>0 and e['lastSalePrice'] is not None and len(e['lastSalePrice'])>0 and e['netChange'] is not None and len(e['netChange'])>0):
      # if(verbose): print(e)
      
      prices[f"{e['symbol']}|{e['assetClass']}"] = {
                                                'price':float(e['lastSalePrice'].replace("$","")),
                                                'vol':int(e['volume'].replace(",","")),
                                                'open':float(e['lastSalePrice'].replace("$",""))-(float(e['netChange']) if e['netChange']!='UNCH' else 0)
                                                }

  return prices
  

def toutc(localtime,localtz):
  return localtz.localize(localtime).astimezone(pytz.utc)

#return time till the next market open in seconds
def timeTillOpen(verbose=False):
  while True:
    try:
      r = json.loads(robreq(f"{BASEURL}/market-info",headers=HEADERS,timeout=5).text)
      opentime = r['data']['marketOpeningTime'][:-3] #get the close time and strip off the timezone (" ET")
      if(verbose): print(opentime)

      #convert to dt object and set to utc
      opentime = toutc(dt.datetime.strptime(opentime,"%b %d, %Y %I:%M %p"),nytz)
      if(verbose): print(opentime)
      
      tto = int((opentime-toutc(dt.datetime.now(),localtz)).total_seconds())
      if(verbose): print(tto)
      
      break
    except Exception:
      print("Error encountered in nasdaq timeTillOpen. Trying again...")
      time.sleep(3)
      pass
    
  if(tto<0): #if it's the same day but after opening
    if(verbose): print("Time estimate to nearest minute")
    nextTradeDate = dt.datetime.strptime(r['data']['nextTradeDate'],"%b %d, %Y") #don't use nextTradeDate() since we already have the data
    thisOpenTime = (dt.datetime.strptime(r['data']['marketOpeningTime'][:-3],"%b %d, %Y %I:%M %p")).time()
    nextOpen = toutc(dt.datetime.combine(nextTradeDate,thisOpenTime),nytz)
    tto = int((nextOpen-toutc(dt.datetime.now(),localtz)).total_seconds())
    
  return tto

#get the time till the next market close in seconds
def timeTillClose(verbose=False):
  while True:
    try:
      r = json.loads(robreq(f"{BASEURL}/market-info",headers=HEADERS,timeout=5).text)
      closetime = r['data']['marketClosingTime'][:-3] #get the close time and strip off the timezone (" ET")
      
      #convert to dt object and set to utc
      closetime = toutc(dt.datetime.strptime(closetime,"%b %d, %Y %I:%M %p"),nytz)
      if(verbose): print(closetime)
      
      ttc = int((closetime-toutc(dt.datetime.now(),localtz)).total_seconds())
      if(verbose): print(ttc)

      break
    except Exception:
      print("Error encountered in nasdaq timeTillClose. Trying again...")
      time.sleep(3)
      pass
  
  if(ttc<0): #if it's the evening
    print("Time estimate to nearest minute")
    nextTradeDate = dt.datetime.strptime(r['data']['nextTradeDate'],"%b %d, %Y")
    thisCloseTime = (dt.datetime.strptime(r['data']['marketClosingTime'][:-3],"%b %d, %Y %I:%M %p")).time()
    nextClose = toutc(dt.datetime.combine(nextTradeDate,thisCloseTime),nytz)
    ttc = int((nextClose-toutc(dt.datetime.now(),localtz)).total_seconds())
  
  return ttc

#return the next market close time as dt object with tz=nyc, and time as utc
def closeTime(verbose=False):
  while True:
    try:
      r = json.loads(robreq(f"{BASEURL}/market-info",headers=HEADERS,timeout=5).text)
      #get the close time and strip off the timezone (" ET")
      closetime = r['data']['marketClosingTime'][:-3]
      #convert to UTC tz
      closetime = toutc(dt.datetime.strptime(closetime,"%b %d, %Y %I:%M %p"),nytz)
      break
    except Exception:
      print("Error encountered in nasdaq closeTime. Trying again...")
      time.sleep(3)
      pass
  return closetime


#determine if the market is currently open or not
def marketIsOpen():
  while True:
    try:
      r = json.loads(robreq(f"{BASEURL}/market-info",headers=HEADERS,timeout=5).text)
      isOpen = "Open" in r['data']['marketIndicator']
      break
    except Exception:
      print("Error encountered in nasdaq marketIsOpen. Trying again...")
      time.sleep(3)
      pass
  return isOpen

#get the earning calls for the last year (date, forecasted, and actual) - dict of {date(mm/dd/yyyy):{forecast,actual}}
def getEarnSurp(symb, maxTries=3):
  tries=0
  out = {}
  while tries<maxTries:
    try:
      r = json.loads(robreq(f"{BASEURL}/company/{symb}/earnings-surprise",headers=HEADERS,timeout=5).content)
      if(r['status']['bCodeMessage'] is None): #valid response
        out = {e['dateReported']:{'forecast':(float(e['consensusForecast']) if e['consensusForecast'] != "N/A" else None),'actual':e['eps']} for e in r['data']['earningsSurpriseTable']['rows']}
      else: #got a valid return, but bad data was passed
        print(r['status']['bCodeMessage'][0]['errorMessage'])
      break
    except Exception:
      print(f"No connection or other error encountered in getEarnSurp for {symb}. Trying again...")
      tries += 1
      time.sleep(3)
      continue
  return out


#get institutional activity for a given stock
#returns dict of format {"increased":{"holders":#,"shares":#},"decreased":{},"held":{}}
def getInstAct(symb, maxTries=3):
  tries=0
  out = {"increased":{"holders":0,"shares":0},"decreased":{"holders":0,"shares":0},"held":{"holders":0,"shares":0}} #init to 0 values
  while tries<maxTries:
    try:
      # could also look here for more info: https://www.holdingschannel.com/
      r = json.loads(robreq(f"{BASEURL}/company/{symb}/institutional-holdings",headers=HEADERS,timeout=5).content)
      if(r['status']['bCodeMessage'] is None): #valid response
        out = r['data']['activePositions']['rows'] #isolate to increased, decreased, held
        out = {e['positions'].split(" ")[0].lower():{"holders":int(e['holders'].replace(',','')),"shares":int(e['shares'].replace(',',''))} for e in out}
      else: #got a valid return, but bad data was passed
        print(f"getInstAct Error {symb}: "+r['status']['bCodeMessage'][0]['errorMessage'])
      break
    except Exception:
      print(f"No connection or other error occured in getInstAct for {symb}. Trying again ({tries+1}/{maxTries})...")
      tries+=1
      time.sleep(3)
      continue
  return out

#get previous 4 quarters and upcoming 4 quarters eps for a given stock
#return dict of format {date:eps}
def getEPS(symb, maxTries=3):
  tries=0
  out = {}
  while tries<maxTries:
    try:
      r = json.loads(robreq(f"{BASEURL}/quote/{symb}/eps",headers=HEADERS,timeout=5).content)
      if(r['status']['bCodeMessage'] is None): #valid response
        if(r['data']['earningsPerShare'] is not None):
          r = r['data']['earningsPerShare']
        else:
          r = {}
      else: #got a valid return, but bad data was passed
        print(r['status']['bCodeMessage'][0]['errorMessage'])
      break
    except Exception:
      print(f"No connection or other error encountered in getEPS for {symb}. Trying again...")
      tries += 1
      time.sleep(3)
      continue
  
  #for every element in the list
  for e in r:
    if("Previous" in e['type']):
      out[e['period']] = {"consensus":e['consensus'],"earnings":e['earnings']}
  
  return out

#get upcoming earning forecasts
def getEarnFcast(symb, maxTries=3):
  tries=0
  out = {}
  while tries<maxTries:
    try:
      r = json.loads(robreq(f"{BASEURL}/analyst/{symb}/earnings-forecast",headers=HEADERS,timeout=5).content)
      if(r['status']['bCodeMessage'] is None): #valid response
        if(r['data']['quarterlyForecast'] is not None):
          r = r['data']['quarterlyForecast']['rows']
        else:
          r = {}
      else: #got a valid return, but bad data was passed
        print(r['status']['bCodeMessage'][0]['errorMessage'])
      break
    except Exception:
      print(f"No connection or other error encountered in getEarnFcast for {symb}. Trying again...")
      tries += 1
      time.sleep(3)
      continue
  
  #for every element in the list
  for e in r:
    out[e['fiscalEnd']] = {"consensus":e['consensusEPSForecast'],"low":e['lowEPSForecast'],"high":e['highEPSForecast'],"estno":e['noOfEstimates']}
  
  return out


#get the shorting interest of a given stock
def getShortInt(symb, maxTries=3):
  tries=0
  out = {}
  while tries<maxTries:
    try:
      r = json.loads(robreq(f"{BASEURL}/quote/{symb}/short-interest?assetclass=stocks",headers=HEADERS,timeout=5).content)
      if(r['status']['bCodeMessage'] is None): #valid response
        r = r['data']['shortInterestTable']['rows']
      else: #got a valid return, but bad data was passed
        print(r['status']['bCodeMessage'][0]['errorMessage'])
      break
    except Exception:
      print(f"No connection or other error encountered in getEarnFcast for {symb}. Trying again...")
      tries += 1
      time.sleep(3)
      continue
  
  #for every element in the list
  for e in r:
    out[e['settlementDate']] = {"interest":int(e['interest'].replace(",","")),"avgDailyShareVol":int(e['avgDailyShareVolume'].replace(",","")),"days2cover":e['daysToCover']}
  
  return out


#get the company financials for the quarters of the last year
# TODO: this is incomplete. data should be formatted as {sheetName:{date:{rows}}}
def getFinancials(symb,maxTries=3):
  tries=0
  out = {}
  while tries<maxTries:
    try:
      r = json.loads(robreq(f"{BASEURL}/company/{symb}/financials?frequency=2",headers=HEADERS,timeout=5).content)
      if(r['status']['bCodeMessage'] is None): #valid response
        out['income'] = r['data']['incomeStatementTable']
        out['balance'] = r['data']['balanceSheetTable']
        out['cashflow'] = r['data']['cashFlowTable']
        out['finratios'] = r['data']['financialRatiosTable']
      else: #got a valid return, but bad data was passed
        print(r['status']['bCodeMessage'][0]['errorMessage'])
      break
    except Exception:
      print(f"No connection or other error encountered in getFinancials for {symb}. Trying again...")
      tries += 1
      time.sleep(3)
      continue
  
  #for every element in the list
  for e in out:
    out[e] = {out[e]['headers']['value2']}
  
  return out



#get the insider trades of a company
#returns the data part of the request (no modifications)
def getInsideTrades(symb, maxTries=3):
  tries=0
  out = {}
  while tries<maxTries:
    try:
      r = json.loads(robreq(f"{BASEURL}/company/{symb}/insider-trades",headers=HEADERS,timeout=5).content)
      if(r['status']['bCodeMessage'] is None): #valid response
        out = r['data']
      else: #got a valid return, but bad data was passed
        print(r['status'])
      break
    except Exception:
      print(f"No connection or other error encountered in getInsideTrades for {symb}. Trying again...")
      tries += 1
      time.sleep(3)
      continue
  
  return out

#get the analyst ratings of a given stock
# returns a list of format [meanRating(text), #ofBrokers(#)]
def getRating(symb, maxTries=3):
  tries=0
  rate = []
  while tries<maxTries:
    try:
      r = json.loads(robreq(f"{BASEURL}/analyst/{symb}/ratings",headers=HEADERS,timeout=5).text)['data']
      if(r is not None and len(r['brokerNames'])>0):
        rate = [r['meanRatingType'],len(r['brokerNames'])]
      break
    except Exception:
      tries+=1
      print(f"No connection or other error encountered in getRating for {symb}. Trying again...")
      time.sleep(3)
      continue
  
  return rate


#calculate the rsi (relative strength index) based on the most recent history of lenth per (hist is output of getHistory)
def getRSI(hist,per=14):
  if(per<len(hist)): #ensure that there's enough info to calculate it
    difs = [float(hist[i][1])/float(hist[i+1][1]) for i in range(per)] #get the daily changes
    avgGain = mean([e for e in difs if e>1])
    avgLoss = mean([e for e in difs if e<1])
    rsi = 1-(1/(1+avgGain/avgLoss)) #value between 0 and 1
    return rsi
  else:
    print("not enough info to calculate rsi")
    return 0

#where priceList is the list of prices to get an EMA of (with newest first)
#k is the exponential factor
#maxPrices is the maximum number of prices to use
def getEMA(priceList,k,maxPrices=750):
  if(len(priceList)>maxPrices): print("too many prices")
  if(1<len(priceList)<=maxPrices):
    return (priceList[0]*k)+(getEMA(priceList[1:],k)*(1-k))
  else:
    return priceList[0]
  
#get the EMAs for all prices in a given set
def getEMAs(priceList,n):
  #assume newest last
  if(len(priceList)>=n):
    out = [None for _ in range(n-1)]+[sum(priceList[:n])/n]
    k = 2/(1+n)
    for p in priceList[n:]:
      out += [k*(p-out[-1])+out[-1]]
    return out
  else:
    print("Not enough data for that window")
    return []


#get the target price of an earning analysis
#return the data part of the request (no modifications)
def getTargetPrice(symb):
  r = json.loads(robreq(f"{BASEURL}/analyst/{symb}/targetprice",headers=HEADERS,timeout=5).text)
  if(r['data'] is not None): r = r['data']
  
  return r
