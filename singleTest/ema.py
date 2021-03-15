#this file contains functions specifically for the exponential moving average algo
#how can we apply an ema to various stocks?
#https://www.alphaexcapital.com/ema-trading-strategy/
#https://www.investopedia.com/terms/e/ema.asp
#also, an ema can work across multiple exchange types, not just for stocks
#these we want to look for high variance, or else for ones that follow a predictable curve (for 

import otherfxns as o
import statistics as stat

algo = 'ema' #name of the algo
#stocks held by this algo according to the records
# stockList = o.json.loads(open(o.c['file locations']['posList'],'r').read())[algo]


def getList():
  print(f"getting unsorted list for {algo}")
  symbs = getUnsortedList()
  print(f"finding stocks for {algo}")
  goodBuys = [e for e in symbs if goodBuy(e)] #the only time that the first char is a number is if it is a valid/good buy
  print(f"{len(goodBuys)} found for {algo}")
  return goodBuys
 
'''
8 different 'goodBuy' states:
is >1 stdev below ema(L/M/S)

LMS strength
000 w
001 w
010 w
011 g
100 w
101 g
110 w
111 g

S(M+L)
'''
#determine whether the queries symb is a good one to buy or not
def goodBuy(symb):
  print(symb)
  #a good buy is considered if current value is >1 stddev below ema as outlined above
  emaDaysS = int(o.c['ema']['emaDaysS'])
  emaDaysM = int(o.c['ema']['emaDaysM'])
  emaDaysL = int(o.c['ema']['emaDaysL'])
  
  hist = o.getHistory(symb,str(o.dt.date.today()-o.dt.timedelta(int((emaDaysL)*12/5))),str(o.dt.date.today())) #get the history just over the long ema days to look
  
  #get the ema and stdev for the short period
  emaS = getEMA(symb,emaDaysS,hist,0,float(o.c['ema']['smoothing']))
  stdDevS = stat.stdev([float(cl[1][1:]) for cl in hist[0:emaDaysS]])
  
  #get the ema and stdev for the medium period
  emaM = getEMA(symb,emaDaysM,hist,0,float(o.c['ema']['smoothing']))
  stdDevM = stat.stdev([float(cl[1][1:]) for cl in hist[0:emaDaysM]])
  
  #get the ema and stdev for the long period
  emaL = getEMA(symb,emaDaysL,hist,0,float(o.c['ema']['smoothing']))
  stdDevL = stat.stdev([float(cl[1][1:]) for cl in hist[0:emaDaysL]])
  
  # print(emaS,stdDevS)
  # print(emaM,stdDevM)
  # print(emaL,stdDevL)
  curPrice = float(hist[0][1][1:])
  
  isGoodBuy = (curPrice<=emaS-stdDevS) and ((curPrice<=emaM-stdDevM) or (curPrice<=emaL-stdDevL))
  
  return isGoodBuy

#calculating the ema is a recursive function
def getEMA(symb,totalDays,hist,daysAgo,smoothing):
  #ema(today) = (price*(smoothing/(1+days)))+ema(yesterday)*(1-(smoothing/(1+days)))
  if(daysAgo<totalDays):
    emaYest = getEMA(symb,totalDays,hist,daysAgo+1,smoothing)
    #TODO: ensure that hist[x][3] is the closing price
    return (float(hist[0][1][1:])*(smoothing/(1+totalDays)))+emaYest*(1-(smoothing/(1+totalDays)))
  else:
    return sum([float(cl[1][1:]) for cl in hist[daysAgo:daysAgo+totalDays]])/totalDays

#get a list of stocks to be sifted through
def getUnsortedList():
  symbList = []
  url = 'https://www.marketwatch.com/tools/stockresearch/screener/results.asp'
  params = {
            "submit":"Screen",
            "Symbol":"true",
            "ResultsPerPage":"OneHundred",
            "TradesShareEnable":"true",
            "TradesShareMin":o.c['ema']['minPrice'],
            "TradesShareMax":o.c['ema']['maxPrice'],
            "TradeVolEnable":"true",
            "TradeVolMin":o.c['ema']['minVol'],
            "MovAvgEnable":"false", #TODO: experiment whether enabling this makes a big difference
            "MovAvgType":"Underperform",
            "MovAvgTime":"FiftyDay",
            "Exchange":"NASDAQ"
            }
  params['PagingIndex'] = 0 #this will change to show us where in the list we should be - increment by 100 (see ResultsPerPage key)
  
  while True:
    try:
      r = o.requests.get(url, params=params, timeout=5).text
      totalStocks = int(r.split("matches")[0].split("floatleft results")[1].split("of ")[1]) #get the total number of stocks in the list - important because they're spread over multiple pages
      break
    except Exception:
      print("No connection or other error encountered in getList (MW). Trying again...")
      time.sleep(3)
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
        time.sleep(3)
        continue

    table = o.bs(r,'html.parser').find_all('table')[0]
    for e in table.find_all('tr')[1::]:
      symbList.append(e.find_all('td')[0].get_text())
  
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
