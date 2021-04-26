#this file contains functions specifically for the on-balance volume/relative strength index algo
# https://therobusttrader.com/volume-indicators-volume-trading/

'''
if the close of a price bar is higher than the previous price bar close, then obv=curvol+prevobv
if close of price bar is lower that previous close, then obv=prevobv-curvol
if curclose=prevclose, then obv=obvprev

absolute value not too important, but movement/trend is
if there's a huge spike in volume, the signal can be very unreliable
might be good idea to smooth it and take a derivitive? - if positive for multiple periods, then good buy, else good sell?

logic being something like this:
if (derivs over some period of time)>0 and isValid (that is, volume not significantly different than the avg)
might also be good to combine with rsi

rsi = avg gains/avg losses over given time frames
buy when oversold (rsi<30, then comes back>=30) and sell when overbought (rsi>100 then comes back<=70)
'''



import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name


def getList(verbose=True):
  #perform checks to see which one ones will gain
  ul = getUnsortedList()
  # If the price is rising in an uptrend but the volume is reducing or unchanged, it may show that there's little interest in the security, and the price may reverse. Similarly, when the price is rapidly declining but the volume is low, it could mean that the institutional traders are not interested in the price direction. So the price will soon reverse to the upside.
  
  obv=obv_prev +/- currentVol
  
  return goodBuys #return dict of symb:note
  

#get list of stocks from stocksUnder1 and marketWatch lists
def getUnsortedList(verbose=False):
  symbList = list()
  
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
      
      
  if(verbose): print("Getting MarketWatch data...")
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
  
  #now that we have the marketWatch list, let's get the stocksunder1 list - essentially the getPennies() fxn from other files
  if(verbose): print("Getting stocksunder1 data...")
  urlList = ['nasdaq','tech','biotech','marijuana','healthcare','energy'] #the ones not labeled for nasdaq are listed on OTC which we want to avoid
  for e in urlList:  
    if(verbose): print(e+" stock list")
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
  
  
  if(verbose): print("Removing Duplicates...")
  symbList = list(dict.fromkeys(symbList)) #combine and remove duplicates
  
  return symbList


#TODO: this should also account for squeezing
def sellUp(symb=""):
  mainSellUp = float(o.c[algo]['sellUp'])
  if(symb in stockList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  mainSellDn = float(o.c[algo]['sellDn'])
  if(symb in stockList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(o.c[algo]['sellUpDn'])


#get a list of stocks to be sifted through
def getUnsortedList():
  return []