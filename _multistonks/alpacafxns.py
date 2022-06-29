import otherfxns as o


#required parameters are where the keyfile is stored, and whether it's paper trading or not
def init(keyFile,isPaper):
  global HEADERS,ACCTURL,ORDERSURL,POSURL,CLKURL,CALURL,ASSETURL,HISTURL
  
  with open(keyFile,"r") as keyFile:
    apiKeys = o.json.loads(keyFile.read())
    
  if(isPaper):
    APIKEY = apiKeys["ALPACAPAPERKEY"]
    SECRETKEY = apiKeys["ALPACAPAPERSECRETKEY"]
    ENDPOINTURL = apiKeys["ALPACAPAPERURL"]
  else:
    APIKEY = apiKeys["ALPACAKEY"]
    SECRETKEY = apiKeys["ALPACASECRETKEY"]
    ENDPOINTURL = apiKeys["ALPACAURL"]
    
  HEADERS = {"APCA-API-KEY-ID":APIKEY,"APCA-API-SECRET-KEY":SECRETKEY} #headers for data
  
  #alpaca = alpacaapi.REST(APIKEY,SECRETKEY,ENDPOINTURL,api_version="v2")
  ACCTURL = f"{ENDPOINTURL}/v2/account" #account url
  ORDERSURL = f"{ENDPOINTURL}/v2/orders" #orders url
  POSURL = f"{ENDPOINTURL}/v2/positions" #positions url
  CLKURL = f"{ENDPOINTURL}/v2/clock" #clock url
  CALURL = f"{ENDPOINTURL}/v2/calendar" #calendar url
  ASSETURL = f"{ENDPOINTURL}/v2/assets" #asset url
  HISTURL = f"{ENDPOINTURL}/v2/account/portfolio/history" #profile history url


# return string of account info
def getAcct():
  while True:
    try:
      html = o.requests.get(ACCTURL, headers=HEADERS, timeout=5).text
      if("portfolio_value" not in html.lower()): raise ValueError("error returned in normal request.")
      break
    except Exception:
      print("No connection, or other error encountered in getAcct. Trying again...")
      o.time.sleep(3)
      continue

  return o.json.loads(html)

# return currently held positions/stocks/whatever
def getPos():
  while True:
    try:
      html = o.requests.get(POSURL, headers=HEADERS, timeout=5).text
      if("error" in html.lower()): raise ValueError("error returned in normal request.")
      break
    except Exception:
      print("No connection, or other error encountered in getPos. Trying again...")
      o.time.sleep(3)
      continue
  return o.json.loads(html)

# return orders for positions/stocks/whatever
def getOrders():
  while True:
    try:
      html = o.requests.get(ORDERSURL, headers=HEADERS, timeout=5).text
      if("error" in html.lower()): raise ValueError("error returned in normal request.")
      break
    except Exception:
      print("No connection, or other error encountered in getOrders. Trying again...")
      o.time.sleep(3)
      continue

  return o.json.loads(html)

#can prompt the user to consent to removing all orders and positions (starting over from scratch)
#returns 1 if trades were made, 0 if no trades made
def sellAll(isManual=1):
  pos = getPos()
  orders = getOrders()
  if(len(pos)+len(orders)>0):
    if(isManual):
      doit = input('Sell and cancel all positions and orders (y/n)? ')
    else:
      doit="y"

    if(doit=="y"): #user consents
      print("Removing Orders...")
      while True:
        try:
          r = o.requests.delete(ORDERSURL, headers=HEADERS, timeout=5)
          break
        except Exception:
          print("No connection, or other error encountered in sellAll. Trying again...")
          o.time.sleep(3)
          continue
      r = o.json.loads(r.text)
      for e in r:
        print(e["body"]["symbol"])
      print("Orders Cancelled.")
      #sell positions
      for p in pos:
        print("Selling "+p["qty"]+" share(s) of "+p["symbol"])
        createOrder("sell",p["qty"],p["symbol"],"market","day")
      print("Done Selling.")
      return 1
    else:
      print("Selling cancelled.")
      return 0
  else:
    print("No shares held")
    return 0

#where the order ID is the "client_order_id" field in output of createOrder
def getOrderInf(orderID,maxTries=3,verbose=False):
  tries=0
  while tries<maxTries:
    if(verbose): print(tries)
    r = {}
    try:
      if(verbose): print("attempting to get data")
      r = o.requests.get(f"{ORDERSURL}?by_client_order_id={orderID}", headers=HEADERS, timeout=5).text
      if(verbose): print("data obtained")
      try:
        if(verbose): print("loading to json")
        r = json.loads(r)
      except Exception:
        if(verbose): print("failed to load to json")
        if(verbose): print(r)
        r = {}
      break
    except Exception:
      print(f"No connection or other error encountered getting the order {orderID}. Trying again ({tries+1}/{maxTries})...")
      tries+=1
      o.time.sleep(3)
      continue
  return r

#look to buy/sell a position
#TODO: need limit orders to be able to be placed
# https://alpaca.markets/docs/api-documentation/api-v2/orders/
def createOrder(side,
                qty,
                symb,
                orderType="market",
                time_in_force="day",
                useExtended=False,
                limPrice=0,
                maxTries=3,
                verbose=False):
  # if(o.getInfo(symb,['istradable'])['istradable']):
  r = {}
  order = {
    "symbol":symb,
    "qty":qty,
    "type":orderType,
    "side":side,
    "time_in_force":time_in_force,
    "extended_hours":useExtended
  }
  if(orderType=="limit"): #TODO: this returns an error if used. Fix
    order['take_profit'] = {'limit_price':str(limPrice)}
  tries=0
  while tries<maxTries:
    try:
      r = o.requests.post(ORDERSURL, json=order, headers=HEADERS, timeout=5)
      break
    except Exception:
      print(f"No connection, or other error encountered in createOrder. Trying again ({tries+1}/{maxTries})...")
      tries+=1
      o.time.sleep(3)
      continue

  r = o.json.loads(r.text)
  if(verbose): print(json.dumps(r,indent=2))
  try:
    #TODO: add trade info here?
    if(verbose): print(f"Order to {r['side']} {r['qty']} share(s) of {r['symbol']} - {r['status']}")
    return r
  except Exception:
    if(verbose): print(f"Error {side}ing {symb}")
    return r
  # else:
    # return {'symbol':symb,'status':'error'}

#check if the market is open
def marketIsOpen():
  while True:
    try:
      r = o.json.loads(o.requests.get(CLKURL, headers=HEADERS, timeout=5).text)['is_open']
      break
    except Exception:
      print("No connection, or other error encountered in marketIsOpen. Trying again...")
      o.time.sleep(3)
      continue
  return r

#current market time (returns yyyy,mm,dd,sec since midnight)
def marketTime():
  while True:
    try:
      ts = o.json.loads(o.requests.get(CLKURL, headers=HEADERS, timeout=5).text)["timestamp"]
      break
    except Exception:
      print("No connection, or other error encountered in marketTime. Trying again...")
      o.time.sleep(3)
      continue

  ts = o.re.split('[-:T.]',ts[:-2])[:-3]
  ts = [int(ts[0]), int(ts[1]), int(ts[2]), int(ts[3])*3600+int(ts[4])*60+int(ts[5])]
  return ts

#time until next market close - in seconds
def timeTillClose():
  while True:
    try:
      cl = o.json.loads(o.requests.get(CLKURL, headers=HEADERS, timeout=5).text)["next_close"]
      break
    except Exception:
      print("No connection, or other error encountered in timeTillClose. Trying again...")
      o.time.sleep(3)
      continue

  cl = o.re.split('[-:T.]',cl[:-2])
  cl = o.dt.datetime(int(cl[0]),int(cl[1]),int(cl[2]),int(cl[3]),int(cl[4]))
  now = marketTime()
  now = o.dt.datetime(int(now[0]),int(now[1]),int(now[2]),int(now[3]/3600),int(now[3]%3600/60),int(now[3]%60))
  return (cl - now).total_seconds()

#time until next market open - in seconds
def timeTillOpen():
  while True:
    try:
      op = o.json.loads(o.requests.get(CLKURL, headers=HEADERS, timeout=5).text)["next_open"]
      break
    except Exception:
      print("No connection, or other error encountered in timeTillOpen. Trying again...")
      o.time.sleep(3)
      continue

  op = o.re.split('[-:T.]',op[:-2])
  op = o.dt.datetime(int(op[0]),int(op[1]),int(op[2]),int(op[3]),int(op[4]))
  now = marketTime()
  now = o.dt.datetime(int(now[0]),int(now[1]),int(now[2]),int(now[3]/3600),int(now[3]%3600/60),int(now[3]%60))
  return (op - now).total_seconds()

#return the open and close times of a given day (EST)
def openCloseTimes(checkDate): #checkdate of format yyyy-mm-dd
  calParams = {}
  calParams["start"] = checkDate
  calParams["end"] = checkDate
  while True:
    try:
      d = o.json.loads(o.requests.get(CALURL, headers=HEADERS, params=calParams, timeout=5).text)[0]
      #subtract 1 from hours to convert from EST (NYSE time), to CST (my time)
      d["open"] = str(int(d["open"].split(":")[0])-1)+":"+d["open"].split(":")[1]
      d["close"] = str(int(d["close"].split(":")[0])-1)+":"+d["close"].split(":")[1]
      break
    except Exception:
      print("No connection, or other error encountered in openCloseTimes. Trying again...")
      o.time.sleep(3)
      continue
  return [o.dt.datetime.strptime(d["date"]+d["open"],"%Y-%m-%d%H:%M"), o.dt.datetime.strptime(d["date"]+d["close"],"%Y-%m-%d%H:%M")]

# return the current price of the indicated stock
#optinal params can be used to have it use alpaca or non-alpaca apis, or if the function should also return the market cap (related because it's also included in the same api request on the nasdaq api)
def getPrice(symb):
  while True:
    try:
      r = o.requests.get(f'https://data.alpaca.markets/v1/last/stocks/{symb.upper()}',headers=HEADERS, timeout=5).text #send request and store response
      if("error" in r.lower()): raise ValueError("error returned in normal request.")
      break
    except Exception:
      print("No connection, or other error encountered in getPrice. Trying again...")
      o.time.sleep(3)
      continue

  try:
    latestPrice = float(o.json.loads(r)['last']['price'])
    return latestPrice
  except Exception:
    print(f"Invalid Stock - {symb}")
    return 0

#make sure that we can trade it on alpaca too
def isAlpacaTradable(symb):
  while True:
    try:
      tradable = o.requests.get(ASSETURL+"/"+symb, headers=HEADERS, timeout=5).text
      if("error" in tradable.lower()): raise ValueError("error returned in normal request.")
      break
    except Exception:
      print("No connection, or other error encountered in isAlpacaTradable. Trying again...")
      o.time.sleep(3)
      continue
  try:
    return o.json.loads(tradable)['tradable']
  except Exception:
    return False


#make sure that the keys being used to access the api are valid
def checkValidKeys(isPaper):
  while True:
    try:
      test = getAcct()
      break
    except Exception:
      print("No connection, or other error encountered in checkValidKeys. Trying again...")
      o.time.sleep(3)
      continue
  try:
    test = test["status"]
    if(test=="ACTIVE"):
      print(f"Valid keys - active account - {'paper' if isPaper else 'live'} trading")
    else:
      print("Valid keys - inactive account")
  except Exception:
    try:
      test = test['message']
      print("Invalid keys")
    except Exception:
      raise ValueError(f"Unknown issue encountered: {test}")
    o.sys.exit()

#get the trades made on a specified date or date range where the dates are formatted as "yyyy-mm-dd"
def getTrades(startDate,endDate=False, verbose=False, maxTries=3):
  tries=0
  while tries<maxTries:
    try:
      if(not endDate): #no end date set, just use a single day
        #TODO: may return an error if no trades were made in a day (or the specified date is a weekend)
        d = o.json.loads(o.requests.get(ACCTURL+"/activities/FILL", headers=HEADERS, params={"date":startDate}, timeout=5).text)
        if("error" in d.lower()):
          print(d)
          raise ValueError("error returned in normal request.")
      else: #end date is set, make a range
        d=[]
        r = o.json.loads(o.requests.get(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate,"until":endDate}, timeout=5).text)
        d+=r
        while len(r)==100:
          if(verbose): print(len(d))
          r = o.json.loads(o.requests.get(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate,"until":endDate,"page_token":d[-1]['id']}, timeout=5).text)
          d+=r
      break
    except Exception:
      print(f"No connection, or other error encountered in getTrades. Trying again ({tries+1}/{maxTries})...")
      tries+=1
      o.time.sleep(3)
      continue
  return d

#get all trades for a given stock from a given start date to today
def getStockTrades(symb,startDate=str(o.dt.date.today())):
  r = []
  while True:
    try:
      d = o.json.loads(o.requests.get(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate}, timeout=5).text)
      while(len(d)==100 or len(r)==100):
        r = o.json.loads(o.requests.get(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate,"page_token":d[-1]['id']}, timeout=5).text)
        d += r
      break
    except Exception:
      print("No connection, or other error encountered in getStockTrades. Trying again...")
      o.time.sleep(3)
      continue
  
  out = [e for e in d if e['symbol']==symb.upper()]
  
  return out


#get the avg price a stock was bought at since the last sell
#this may be the same as avg_entry_price in getPos, but more experimentation is needed
#TODO: this is out of date and should be fixed
def getBuyPrice(symb):
  '''
  average the stock's buy prices from the minimum of the jump date or when the last sell was
  '''
  #get the latest jump date
  jumpDate = o.goodBuy(symb,200)
  
  try: #make sure that the jump date is valid, if not, try getting the average price paid overall, otherwise just return 0
    jumpDate = str(o.dt.datetime.strptime(jumpDate, "%m/%d/%Y")) #convert to standard yyyy-mm-dd format
  except Exception:
    print("error finding recent jump date")
    try:
      p = getPos()
      avg = float([e for e in p if e['symbol']==symb.upper()][0]['avg_entry_price'])
      print("returning overall average price")
      return avg
    except Exception:
      print("error finding overall average")
      return 0

  t = getStockTrades(symb, jumpDate) #get all trades for the stock
  
  #find the latest sell date
  i=0
  while i<len(t) and t[i]['side']=="buy":
    i += 1
  
  #return the avg, or if no data found (or latest trade was a sell), return 0
  if(i>0):
    totalSpent = sum([float(e['price'])*float(e['qty']) for e in t[:i]])
    totalQty = sum([float(e['qty']) for e in t[:i]])
    return totalSpent/totalQty
  else:
    return 0


#get the account history from the startDate going back some time (#D,W,M,A), default to 1 year from today 
def getProfileHistory(startDate=str(o.dt.date.today()), period='1A'):
  while True:
    try:
      html = o.requests.get(HISTURL, headers=HEADERS, params={'date_end':startDate,'period':period}, timeout=5).text
      break
    except Exception:
      print("No connection, or other error encountered in getProfileHistory. Trying again...")
      o.time.sleep(3)
      continue
  return o.json.loads(html)


#get all transactions from a given start date to today
def getXtns(startDate=str(o.dt.date.today()),actType="TRANS"):
  r = []
  while True:
    try:
      d = o.json.loads(o.requests.get(f"{ACCTURL}/activities/{actType}", headers=HEADERS, params={"after":startDate}, timeout=5).text)
      if("error" in d.lower()): raise ValueError("error returned in normal request.")
      while(len(d)==100 or len(r)==100):
        r = o.json.loads(o.requests.get(f"{ACCTURL}/activities/{actType}", headers=HEADERS, params={"after":startDate,"page_token":d[-1]['id']}, timeout=5).text)
        if("error" in d.lower()): raise ValueError("error returned in normal request.")
        d += r
      break
    except Exception:
      print("No connection, or other error encountered in getXtns. Trying again...")
      o.time.sleep(3)
      continue
  
  out=d #pare down to some specified ones if desired  
  return out
