#this file contains functions specifically for the div algo
#what changes when a stock has a dividend?
#https://www.investopedia.com/articles/stocks/11/dividend-capture-strategy.asp

import otherfxns as o

algo = 'divs' #name of the algo


#stocks held by this algo according to the records
posList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]

def getList():
  #perform checks to see which one ones will gain
  #check history of the stocks. Look for pattern that denotes a gain after the initial div date (could possibly look like a buy low. Stock gains to div, div processes, dips, then gains again. Sell at that gain)
  
  #if today < ex div date, then buy
  

  print(f"getting unsorted list for {algo}")
  symbs = getUnsortedList()
  print(f"finding stocks for {algo}")
  goodBuys = [s for s in symbs if float(o.c[algo]['minPrice'])<=o.getPrice(s)<=float(o.c[algo]['maxPrice']) and o.getVol(s)>=float(o.c[algo]['minVol'])]
  print(f"{len(goodBuys)} found for {algo}")
  return goodBuys
  

#return whether symb is a good sell or not
#if div is collected and price > buyPrice+div, then sell
def goodSell(symb):
  dates = getDivDates(symb)
  if(o.getPrice(symb)/posList[algo][symb]['buyprice']<=sellDn(symb)):
    return True
  elif(str(dt.date.today())>dates['payment'] and
       o.getPrice(symb)/posList[algo][symb]['buyprice']>=sellUp(symb)):
    return True
  else:
    return False

#TODO: this should also account for squeezing
def sellUp(symb=""):
  mainSellUp = float(o.c[algo]['sellUp'])
  if(symb in posList):
    #TODO: add exit condition (see it in getList)
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  mainSellDn = float(o.c[algo]['sellDn'])
  if(symb in posList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(o.c[algo]['sellUpDn'])


#get a list of stocks to be sifted through
def getUnsortedList():
  while True:
    try:
      #
      r = o.json.loads(o.requests.get(f"https://api.nasdaq.com/api/calendar/dividends?date={o.nextTradeDate()}",headers={"user-agent":"-"}, timeout=5).text)['data']['calendar']['rows']
      break
    except Exception:
      print("Error in getting unsorted list for divs algo. Trying again...")
      o.time.sleep(3)
      pass
  
  r = [e['symbol'] for e in r]
  
  return r

#get the latest 4 div dates for a stock (announced, ex div, record, payment)
def getDivDates(symb):
  while True:
    try:
      #
      r = o.json.loads(o.requests.get(f"https://api.nasdaq.com/api/quote/{symb}/dividends?assetclass=stocks&limit=1",headers={"user-agent":"-"}, timeout=5).text)['data']['dividends']['rows'][0]
      break
    except Exception:
      print(f"Error in getting div dates for {symb}. Trying again...")
      o.time.sleep(3)
      pass
    
  r = {
        'announcement':str(o.dt.datetime.strptime(r['declarationDate'],"%m/%d/%Y").date()),
        'ex':str(o.dt.datetime.strptime(r['exOrEffDate'],"%m/%d/%Y").date()),
        'record':str(o.dt.datetime.strptime(r['recordDate'],"%m/%d/%Y").date()),
        'payment':str(o.dt.datetime.strptime(r['paymentDate'],"%m/%d/%Y").date())
      }
  return r