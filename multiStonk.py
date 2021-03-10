import otherfxns as o
import alpacafxns as a
import random, time, json, threading, sys, os
from glob import glob
import datetime as dt
#import the algorithms
sys.path.append(o.c['file locations']['algosDir'])
import dj, fda#, divs #ADD NEW ALGO FUNCTIONS HERE

#http://bettersystemtrader.com/088-protect-and-grow-capital-during-corrections-with-ivanhoff/
#other algo ideas: splits, divs, earnings, ema, forex, gap up, high volume breakout

#TODO: mark to sell if rev splitting (in market close section)

#TODO: add squeezing times? Different for every algo
algoList = {'dj':[],'fda':[]} #list of algorithms to be used and their corresponding stock lists to be bought

#if the posList file doesn't exist
if(not os.path.isfile(o.c['file locations']['posList'])):
  with open(o.c['file locations']['posList'],'w') as f:
    f.write(json.dumps({e:{} for e in algoList}))
  posList = open(o.c['file locations']['posList'],'r').read()
else: #if it does exist
  try: #try reading any json data from it
    #TODO: also check len() to make sure that all algos are present in the list? Might not have to, but will need to be tested
    with open(o.c['file locations']['posList'],'r') as f:
      posList = json.loads(f.read())
      if(len(posList)<len(algoList)):
        #TODO: the following loop could probably be replaced with a single line, something like: posList = {posList[e] for e in algoList if e in posList else algoList[e]}
        for algo in algoList:
          if(algo not in posList):
            posList[algo] = {}
  except Exception: #if it fails, then just write the empty algoList to the file
    #TODO: this is dangerous! This could potentially overwrite all saved position data if there's any error above. Make this more robust
    with open(o.c['file locations']['posList'],'w') as f:
      f.write(json.dumps({e:{} for e in algoList}))
    posList = open(o.c['file locations']['posList'],'r').read()


'''
posList should be structured something like this:
{
  algo1: {
    symb1: {
      sharesheld:##,
      lastTradeDate:##,
      lastTradeType:XX,
      shouldSell:XXXX
    },
    symb2: {
      ...
    }
  },
  algo2: {
    ...
  }
  ...
}
'''


listsUpdatedToday = False

def main():
  global algoList, posList, listsUpdatedToday
  portHist = a.getProfileHistory(str(dt.date.today()),'1M')['equity']
  portHist = [e for e in portHist if e is not None]
  maxPortVal=max(portHist) #get the max portfolio value over the last month
  acct = a.getAcct()
  
  while float(acct['portfolio_value'])>=maxPortVal*float(o.c['account params']['portStopLoss']): 
    
    acct = a.getAcct() #get account info
    pos = a.getPos() #get all held positions (no algo assigned)
    
    if(a.marketIsOpen()):
      #update the lists if not updated yet
      print(f"Portfolio Value: ${acct['portfolio_value']}, total cash: ${acct['cash']}")
      if(not listsUpdatedToday):
        updateLists()
      
      #look to sell things
      for algo in algoList:
        print(f"{algo} stocks")
        check2sell(algo,pos) #only look at the ones currently held
      
      if(a.timeTillClose()<60*float(o.c['time params']['buyTime']) and sum([t.getName().startswith('update') for t in threading.enumerate()])==0):
        tradableCash = float(acct['cash']) if float(acct['cash'])<float(o.c['account params']['cash2hold']) else max(float(acct['cash'])-float(o.c['account params']['cash2hold'])*float(o.c['account params']['cashMargin']),0) #account for withholding a certain amount of cash+margin
        cashPerAlgo = tradableCash/len(algoList) #evenly split available cash across all algos
        #start buying things
        for e in algoList:
          buyThread = threading.Thread(target=check2buy, args=(e,cashPerAlgo, algoList[e])) #init the thread - note locking is required here
          buyThread.setName(e) #set the name to the stock symb
          buyThread.start() #start the thread
    
      time.sleep(60)
    
    else: #market is closed
      #update the max port val
      print("Updating max portfolio value")
      portHist = a.getProfileHistory(str(dt.date.today()),'1M')['equity']
      portHist = [e for e in portHist if e is not None]
      maxPortVal=max(portHist)

      #TODO: sync up posList and if there are any positions that are held that aren't accounted for in an algo (or vise versa, an algo thinks there are shares when there aren't)
      if(o.dt.date.today().weekday()==4 and o.dt.datetime.now().time()>o.dt.time(12)): #if it's friday afternoon
        #delete all csv files in stockDataDir
        print("Removing saved csv files")
        for f in glob(o.c['file locations']['stockDataDir']+"*.csv"):
          o.os.unlink(f)
        
        #remove all stocks in the stock list that aren't currently held
        pos = [e['symbol'] for e in a.getPos()] #isolate just the symbols
        for algo in algoList: #look at every algo
          for e in algoList[algo]: #look at every stock in the algo
            if(e not in pos): #if it's not held
              algoList[algo].pop(e) #remove it
      
      # clear all lists in algoList
      print("Clearing stock lists")
      algoList = {e:[] for e in algoList}
      
      tto = a.timeTillOpen()
      print(f"Market opens in {round(tto/3600,2)} hours")
      #wait some time before the market opens      
      if(tto>60*float(o.c['time params']['updateLists'])):
        print(f"Updating stock lists in {round((tto-60*float(o.c['time params']['updateLists']))/3600,2)} hours")
        time.sleep(tto-60*float(o.c['time params']['updateLists']))
      #update stock lists
      updateLists()
      
      time.sleep(a.timeTillOpen())
      
  
  #TODO: in live version, this should be false
  a.sellAll(isManual=True) #if the portfolio value falls below our stop loss, automatically sell everything

#update all lists to be bought
def updateLists():
  global algoList, listsUpdatedToday
  lock = threading.Lock()
  revSplits = o.reverseSplitters()
  for e in algoList: #start a thread to update the list for each algorithm
    if(len(algoList[e])==0): #TODO: might not actually need to do this check
      print(f"updating {e} list")
      updateThread = threading.Thread(target=updateList, args=(e,lock,revSplits)) #init the thread - note locking is required here
      updateThread.setName("update-"+e) #set the name to the stock symb
      updateThread.start() #start the thread
      
    #TODO: see the following because the updateList threads currently all access
    # https://www.geeksforgeeks.org/multithreading-in-python-set-2-synchronization/
    
  listsUpdatedToday = True #TODO: see link also for sync and where this should be/how this should be set so that it updates when all these threads are completed (may need to run this function as its own thread as well?)


#update the to-buy list of the given algorithm, and exclude a list of rm stocks
def updateList(algo,lock,rm=[]):
  global algoList
  algoBuys = eval(algo+".getList()") #this is probably not safe, but best way I can think of
  algoBuys = [e for e in algoBuys if e not in rm] #remove any stocks that are in the rm list
  lock.acquire() #lock in order to write to the list
  algoList[algo] = algoBuys
  lock.release() #then unlock

#check to sell positions from a given algo (where algo is an aglo name, and pos is the output of a.getPos())
def check2sell(algo, pos):
  sellUp = eval(algo+".sellUp()")
  sellDn = eval(algo+".sellDn()")
  #TODO: check that # of shares to sell (and in triggered up) is >0
  for e in pos: #TODO: check last trade date/type
    if(e['symbol'] in posList[algo]):
      curPrice = a.getPrice(e['symbol'])
      print(f"{algo}\t{round(curPrice,2)}\t{round(sellUp,2)} & {round(sellDn,2)}")
      if(shouldSell or curPrice<e['avg_buy_price']*sellDn):
        sell(e['symbol'],algo) #record and everything in the sell function
      elif(curPrice>=sellUp):
        #TODO: look at locking if need be
        triggerThread = threading.Thread(target=triggeredUp, args=(e['symbol'],algo)) #init the thread - note locking is required here
        triggerThread.setName(e['symbol']) #set the name to the stock symb
        triggerThread.start() #start the thread
        

#TODO: add comments
def check2buy(algo, cashAvailable, stocks2buy):
  global posList
  cashPerStock = cashAvailable/len(stocks2buy)
  #TODO: stocks2buy should be shuffled. Also other printing should happen rather than printing the actual response
  #TODO: also, this should probably loop forever/until a certain condition is met, and also needs to check that a stock isn't already trying to sell, and that this thread isn't already running

  for stock in stocks2buy:
    if(stock not in posList[algo]):
      posList[algo][stock] = {
          "sharesheld":0,
          "lastTradeDate":str(dt.date.today()),
          "lastTradeType":"NA",
          "shouldSell":False
        }
    stockInfo = posList[algo][stock]
    if dt.datetime.strptime(posList[algo][stock]['lastTradeDate'],"%Y-%m-%d").date() < dt.date.today() or posList[algo][stock]['lastTradeType']!="sell":
      shares = int(cashPerStock/a.getPrice(stock))
      if(shares>0):
        buy(int(cashPerStock/a.getPrice(stock)),stock,algo)
    

def triggeredUp(stock, algo):
  maxPrice = 0
  curPrice = 0
  sellUpDn = eval(algo+".sellUpDn()")
  while(curPrice>=maxPrice*sellUpDn and a.timeTillClose()>30):
    curPrice = a.getPrice(stock)
    maxPrice = max(maxPrice,curPrice)
    print(f"{algo}\t{stock}\t{round(curPrice,2)} : {round(maxPrice,2)}")
    time.sleep(3) #slow it down a little bit
  sell(stock, algo)


def sell(stock, algo):
  #basically just a market order for the stock and then record it into an order info file
  r = a.createOrder("sell",inf[algo][stock]['shares held'],stock)
  
  if(r['status'] == "accepted"):
    inf[algo][stock] = {
        "sharesheld":0,
        "lastTradeDate":str(dt.date.today()),
        "lastTradeType":"sell",
        "shouldSell":False
      }
    return True
  else:
    return False

def buy(shares, stock, algo):
  #basically just a market buy of this many shares of this stock for this algo
  global posList #TODO: may need to incorporate locking
  r = a.createOrder("buy",shares,stock)
  print(r)
  if(r['status'] == "accepted"):
    posList[algo][stock] = {
        "sharesheld":r['qty'],
        "lastTradeDate":str(dt.date.today()),
        "lastTradeType":"buy",
        "shouldSell":False
      }
    
    return True
  else:
    return False



#run the main function
if __name__ == '__main__':
  print("\nStarting up...\n")
  a.checkValidKeys()
  
  if(len(a.getPos())==0): #if the trader doesn't have any stocks (i.e. they've not used this algo yet), then give them a little more info
    print("Will start buying "+str(o.c['time params']['buyTime'])+" minutes before next close")

  main()
