import ndaqfxns as n
import json,time
import datetime as dt

#required parameters are where the keyfile is stored, and whether it's paper trading or not
def init(keyFile,isPaper):
  global HEADERS,ACCTURL,ORDERSURL,POSURL,CLKURL,CALURL,ASSETURL,HISTURL
  
  with open(keyFile,"r") as keyFile:
    apiKeys = json.loads(keyFile.read())
    
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
  html = n.robreq(ACCTURL, headers=HEADERS, timeout=5, maxTries=-1).text
  if("portfolio_value" not in html.lower()):
    print("error in data from getAcct")
  return json.loads(html)

# return currently held positions/stocks/whatever
def getPos():
  html = n.robreq(POSURL, headers=HEADERS, timeout=5, maxTries=-1).text
  if("error" in html.lower()):
    print("error in data from getPos")
  return json.loads(html)

# return orders for a specified param
#valid 
#status=open|closed|all (which orders to return) - default to open
#limit=max number of orders per response - default to 50
#after=only orders after this timestamp (format yyyy-mm-ddThh:mm:ssZ)
#until=only orders until this timestamp (format strftime(dt.datetime(),"%Y-%m-%dT%H:%M:%SZ") - same as above)
#direction=asc|desc chronilogical order of response - default to desc
#nested=bool (not using this for now)
#symbols=comma seperated list of symbols to get orders of ex:"AAPL,MSFT,GOOG"
#qty_above=### only orders above the given qty
#qty_below=### only order below the given qty
#https://alpaca.markets/docs/api-references/broker-api/trading/orders/#getting-all-orders
def getOrders(params={"status":None,"limit":None,"after":None,"until":None,"direction":None,"nested":None,"symbols":None,"qty_above":None,"qty_below":None},verbose=False):
  
  if(verbose): print("input params:",params)
  
  #remove all empty elements
  params = {e:params[e] for e in params if params[e] is not None}
  
  if(verbose): print("parsed params:",params)
  
  html = n.robreq(url=ORDERSURL,headers=HEADERS,params=params,timeout=5, maxTries=-1)
  if(verbose): print("raw html",html.text)
  return html.json()

#close all orders and positions (liquidate everything. Bascially the big red STOP button)
#can prompt the user to consent to removing all orders and positions (starting over from scratch)
#returns 1 if trades were made, 0 if no trades made
def closeAll(isManual=1):
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
          r = n.robreq(ORDERSURL, method="delete", headers=HEADERS, timeout=5, maxTries=-1)
          break
        except Exception:
          print("No connection, or other error encountered in closeAll. Trying again...")
          time.sleep(3)
          continue
      r = json.loads(r.text)
      for e in r:
        if('body' in e): print(e["body"]["symbol"])
        else: print(e['id'])
      print("Orders Cancelled.")
      #close positions (sell longed, buy shorted)
      for p in pos:
        if(float(p['qty'])>0):
          print("Selling "+p["qty"]+" share(s) of "+p["symbol"])
          createOrder(side="sell",qty=float(p["qty"]),symb=p["symbol"],orderType="market",time_in_force="day")
        else:
          print(f"Buying {abs(float(p['qty']))} share(s) of {p['symbol']}")
          createOrder(side="buy",qty=abs(float(p["qty"])),symb=p["symbol"],orderType="market",time_in_force="day")
          
      print("Done trading.")
      return 1
    else:
      print("Closing cancelled.")
      return 0
  else:
    print("No shares held")
    return 0

#where the order ID is the "client_order_id" field in output of createOrder
#TODO: clean this function up
def getOrderInf(orderID,maxTries=3,verbose=False):
  tries=0
  while tries<maxTries:
    if(verbose): print(tries)
    r = {}
    try:
      if(verbose): print("attempting to get data")
      r = n.robreq(f"{ORDERSURL}?by_client_order_id={orderID}", headers=HEADERS, timeout=5, maxTries=-1).text
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
      time.sleep(3)
      continue
  return r

#close a specified order by a given ID
# https://alpaca.markets/docs/api-references/broker-api/trading/orders/#deleting-an-order-by-order-id
def closeOrder(orderID,verbose=False):
  r = n.robreq(f"{ORDERURL}/{orderID}",method="delete",headers=HEADERS)
  if("error" in r.text.lower()):
    if(verbose): print(f"error occured while attempting to close order {orderID}")

  return r.json()

#create an order to trade a stock
# https://alpaca.markets/docs/api-documentation/api-v2/orders/
def createOrder(symb, #stock ticker symbol
                side, #buy|sell
                orderType="market", #market|limit|stop|stop_limit|trailing_stop
                time_in_force="day", #day|gtc|opg|cls|ioc|fok
                
                qty=0, #number of shares to trade (use in lieu of price)
                notional=0, #dollar amt to trade (in lieu of qty)
                
                limit_price=0, #execute the order at the specified price
                stop_price=0, #trigger an order after this is reached - see: https://www.investopedia.com/ask/answers/04/022704.asp
                trail_price=0, #set a price to trail at (use in lieu of trail_percent)
                trail_percent=0, #set a percent to trail at (use in lieu of trail_price)
                
                extended_hours=False, #if true, order can be traded in pre/after market hours
                orderID="", #specify a UID for the trade
                order_class=None, #simple|bracket|oco|oto (defaults to simple)
                take_profit=None, #specify a take profit price
                stop_loss=None, #specify a stop loss price
                
                maxTries=3,
                verbose=False):
  
  #clean input
  symb = str(symb).upper()
  side = str(side).lower()
  orderType = str(orderType).lower()
  time_in_force = str(time_in_force).lower()
  qty = str(float(qty))
  notional = str(float(notional))
  limit_price = str(float(limit_price))
  stop_price = str(float(stop_price))
  trail_price = str(float(trail_price))
  trail_percent = str(float(trail_percent))
  orderID = str(orderID)[:48] #maxes out at 48 chars
  order_class = str(order_class).lower()
  #TODO: clean take_profit and stop_loss as needed
  
  #init response object
  r = {}
  
  #common required for all trade types:
  order = {
    "symbol":symb.upper(),
    "type":orderType,
    "side":side,
    "time_in_force":time_in_force
  }
  #ensure the quantity or price is set
  if(float(qty)==0 and float(notional)!=0):
    order['notional'] = notional
  elif(float(notional)==0 and float(qty)!=0):
    order['qty'] = qty
  else:
    raise ValueError(f"Must set price or quantity. Price set to {notional}, qty set to {qty}")
  
  
  #other required params (throw an error if not present)
  
  if(orderType in ["limit","stop_limit"]):
    if(limit_price!=0): order['limit_price'] = limit_price
    else: raise ValueError("limit price required for limit or stop_limit")
  
  if(orderType in ['stop','stop_limit']):
    if(stop_price!=0): order['stop_price'] = stop_price
    else: raise ValueError("stop price required for stop or stop_limit")
  
  elif(orderType=='trailing_stop'):
    if(float(trail_price)==0 and float(trail_percent)!=0):
      order['trail_percent']=trail_percent
    elif(float(trail_price)!=0 and float(trail_percent)==0):
      order['trail_price']=trail_price
    else:
      raise ValueError(f"trail price ({trail_price}) or percent ({trail_percent}) must be set for trailing stop type")
  
  
  # optional params
  if(orderType=='limit' and time_in_force=='day'): order['extended_hours']=extended_hours
  if(0<len(orderID)<=48):order['client_order_id']=orderID
  if(order_class in ['simple','bracket','oco','oto']): order['order_class']=order_class
  
  
  #specify stuff for bracket style orders
  #https://alpaca.markets/docs/trading/orders/#bracket-orders
  if(order_class=='bracket'):
    if(take_profit is not None):
      order['take_profit']=take_profit
    else:
      raise ValueError("bracket requires take profit")
    if(stop_loss is not None):
      order['stop_loss']=stop_loss
    else:
        raise ValueError("bracket requires stop loss")
  
  if(order_class=='oto'):
    if(stop_loss is not None and take_profit is None):
      order['stop_loss']=stop_loss
    elif(stop_loss is None and take_profit is not None):
      order['take_profit']=take_profit
    else:
      raise ValueError("oto requires either sl OR tp to be specified")
  
  tries=0
  while tries<maxTries:
    try:
      r = n.robreq(ORDERSURL, method="post", jsondata=order, headers=HEADERS, timeout=5, maxTries=-1)
      break
    except Exception:
      print(f"No connection, or other error encountered in createOrder. Trying again ({tries+1}/{maxTries})...")
      tries+=1
      time.sleep(3)
      continue

  r = json.loads(r.text)
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

#TODO:
#https://alpaca.markets/docs/api-references/trading-api/orders/#replace-an-order
def replaceOrder():
  return False

#check if the market is open
def marketIsOpen():
  while True:
    try:
      r = json.loads(n.robreq(CLKURL, headers=HEADERS, timeout=5, maxTries=-1).text)['is_open']
      break
    except Exception:
      print("No connection, or other error encountered in marketIsOpen. Trying again...")
      time.sleep(3)
      continue
  return r

#current market time (returns yyyy,mm,dd,sec since midnight)
def marketTime():
  while True:
    try:
      ts = json.loads(n.robreq(CLKURL, headers=HEADERS, timeout=5, maxTries=-1).text)["timestamp"]
      break
    except Exception:
      print("No connection, or other error encountered in marketTime. Trying again...")
      time.sleep(3)
      continue

  ts = n.re.split('[-:T.]',ts[:-2])[:-3]
  ts = [int(ts[0]), int(ts[1]), int(ts[2]), int(ts[3])*3600+int(ts[4])*60+int(ts[5])]
  return ts

#time until next market close - in seconds
def timeTillClose():
  while True:
    try:
      cl = json.loads(n.robreq(CLKURL, headers=HEADERS, timeout=5, maxTries=-1).text)["next_close"]
      break
    except Exception:
      print("No connection, or other error encountered in timeTillClose. Trying again...")
      time.sleep(3)
      continue

  cl = n.re.split('[-:T.]',cl[:-2])
  cl = dt.datetime(int(cl[0]),int(cl[1]),int(cl[2]),int(cl[3]),int(cl[4]))
  now = marketTime()
  now = dt.datetime(int(now[0]),int(now[1]),int(now[2]),int(now[3]/3600),int(now[3]%3600/60),int(now[3]%60))
  return (cl - now).total_seconds()

#time until next market open - in seconds
def timeTillOpen():
  while True:
    try:
      op = json.loads(n.robreq(CLKURL, headers=HEADERS, timeout=5, maxTries=-1).text)["next_open"]
      break
    except Exception:
      print("No connection, or other error encountered in timeTillOpen. Trying again...")
      time.sleep(3)
      continue

  op = n.re.split('[-:T.]',op[:-2])
  op = dt.datetime(int(op[0]),int(op[1]),int(op[2]),int(op[3]),int(op[4]))
  now = marketTime()
  now = dt.datetime(int(now[0]),int(now[1]),int(now[2]),int(now[3]/3600),int(now[3]%3600/60),int(now[3]%60))
  return (op - now).total_seconds()

#return the open and close times of a given day (EST)
def openCloseTimes(checkDate): #checkdate of format yyyy-mm-dd
  calParams = {}
  calParams["start"] = checkDate
  calParams["end"] = checkDate
  while True:
    try:
      d = json.loads(n.robreq(CALURL, headers=HEADERS, params=calParams, timeout=5, maxTries=-1).text)[0]
      #subtract 1 from hours to convert from EST (NYSE time), to CST (my time)
      d["open"] = str(int(d["open"].split(":")[0])-1)+":"+d["open"].split(":")[1]
      d["close"] = str(int(d["close"].split(":")[0])-1)+":"+d["close"].split(":")[1]
      break
    except Exception:
      print("No connection, or other error encountered in openCloseTimes. Trying again...")
      time.sleep(3)
      continue
  return [dt.datetime.strptime(d["date"]+d["open"],"%Y-%m-%d%H:%M"), dt.datetime.strptime(d["date"]+d["close"],"%Y-%m-%d%H:%M")]

# return the current price of the indicated stock
#optinal params can be used to have it use alpaca or non-alpaca apis, or if the function should also return the market cap (related because it's also included in the same api request on the nasdaq api)
def getPrice(symb,verbose=False):
  symb = symb.upper()
  r={}
  #attempt to request until anything valid is returned
  while('trade' not in r and 'code' not in r):
    r = n.robreq(f'https://data.alpaca.markets/v2/stocks/{symb}/trades/latest',headers=HEADERS,timeout=5, maxTries=-1).json() #send request and store response
    if(verbose): print(r)
  
  if('trade' in r):
    return r['trade']['p']
  else:
    print(r)
    return -1
  

#make sure that we can trade it on alpaca too
#specify the side
def isAlpacaTradable(symb,isLong=True):
  symb = symb.upper()
  r = n.robreq(ASSETURL+"/"+symb, headers=HEADERS, timeout=5, maxTries=-1).json()
  try:
    if(isLong):
      return r['tradable']
    else:
      #ensure that it's also easy to borrow when shorting
      return r['shortable'] and r['easy_to_borrow']
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
      time.sleep(3)
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
    n.sys.exit()

#get the trades made on a specified date or date range where the dates are formatted as "yyyy-mm-dd"
def getTrades(startDate,endDate=False, verbose=False, maxTries=3):
  tries=0
  while tries<maxTries:
    try:
      if(not endDate): #no end date set, just use a single day
        #TODO: may return an error if no trades were made in a day (or the specified date is a weekend)
        d = n.robreq(ACCTURL+"/activities/FILL", headers=HEADERS, params={"date":startDate}, timeout=5, maxTries=-1).json()
        if("error" in d.lower()):
          print(d)
          raise ValueError("error returned in normal request.")
      else: #end date is set, make a range
        d=[]
        r = n.robreq(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate,"until":endDate}, timeout=5, maxTries=-1)
        r = r.json()
        if(verbose): print(len(r))
        d+=r
        while len(r)==100:
          if(verbose): print(len(d))
          r = n.robreq(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate,"until":endDate,"page_token":d[-1]['id']}, timeout=5, maxTries=-1).json()
          d+=r
      break
    except Exception:
      print(f"No connection, or other error encountered in getTrades. Trying again ({tries+1}/{maxTries})...")
      tries+=1
      time.sleep(3)
      continue
  return d

#get all trades for a given stock from a given start date to today
def getStockTrades(symb,startDate=str(dt.date.today())):
  symb = symb.upper()
  r = []
  while True:
    try:
      d = json.loads(n.robreq(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate}, timeout=5, maxTries=-1).text)
      while(len(d)==100 or len(r)==100):
        r = json.loads(n.robreq(ACCTURL+"/activities/FILL", headers=HEADERS, params={"after":startDate,"page_token":d[-1]['id']}, timeout=5, maxTries=-1).text)
        d += r
      break
    except Exception:
      print("No connection, or other error encountered in getStockTrades. Trying again...")
      time.sleep(3)
      continue
  
  out = [e for e in d if e['symbol']==symb.upper()]
  
  return out


#get the avg price a stock was bought at since the last sell
#this may be the same as avg_entry_price in getPos, but more experimentation is needed
#TODO: this is out of date and should be fixed
def getBuyPrice(symb):
  symb = symb.upper()
  '''
  average the stock's buy prices from the minimum of the jump date or when the last sell was
  '''
  #get the latest jump date
  jumpDate = n.goodBuy(symb,200)
  
  try: #make sure that the jump date is valid, if not, try getting the average price paid overall, otherwise just return 0
    jumpDate = str(dt.datetime.strptime(jumpDate, "%m/%d/%Y")) #convert to standard yyyy-mm-dd format
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


#get the account value history
#startDate = latest date to look for
#period = #D|#W|#M|#A, default to 1 year ago from today (1A)
#formatted = t|f - True returns dict of format {yyyy-mm-dd-hh-mm:{equity:#,pl:#,plpct:#}}
def getProfileHistory(startDate=str(dt.date.today()), period='1A', formatted=True, verbose=False):
  if(verbose): print(f"attempting to get profile history from {startDate} with a period of {period}")
  while True:
    try:
      r = n.robreq(HISTURL, headers=HEADERS, params={'date_end':startDate,'period':period}, timeout=5, maxTries=-1).json()
      break
    except Exception as e:
      print("No connection, or other error encountered in getProfileHistory. Trying again...")
      print(e)
      time.sleep(3)
      continue

  if(formatted):
    if(verbose): print("formatting...")
    r = {dt.datetime.strftime(dt.datetime.fromtimestamp(r['timestamp'][e]),"%Y-%m-%d-%H-%M"):{"eq":r['equity'][e],"pl":r['profit_loss'][e],"plpct":r['profit_loss_pct'][e]} for e in range(len(r['timestamp']))}
  return r


#get all transactions from a given start date to today
def getXtns(startDate=str(dt.date.today()),actType="TRANS"):
  r = []
  while True:
    try:
      d = json.loads(n.robreq(f"{ACCTURL}/activities/{actType}", headers=HEADERS, params={"after":startDate}, timeout=5, maxTries=-1).text)
      if("error" in d.lower()): raise ValueError("error returned in normal request.")
      while(len(d)==100 or len(r)==100):
        r = json.loads(n.robreq(f"{ACCTURL}/activities/{actType}", headers=HEADERS, params={"after":startDate,"page_token":d[-1]['id']}, timeout=5, maxTries=-1).text)
        if("error" in d.lower()): raise ValueError("error returned in normal request.")
        d += r
      break
    except Exception:
      print("No connection, or other error encountered in getXtns. Trying again...")
      time.sleep(3)
      continue
  
  out=d #pare down to some specified ones if desired  
  return out
