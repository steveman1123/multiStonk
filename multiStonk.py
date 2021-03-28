import otherfxns as o
import alpacafxns as a
import random, time, json, threading, sys, os
from glob import glob
from operator import eq
import datetime as dt


#get the config file
configFile="./configs/multi.config"
if(len(sys.argv)>1): #if there's an argument present
  for arg in sys.argv[1:]:
    if(arg.lower().startswith("configfile=")): #if there's an argument regarding the config file
      configFile = arg.split("=")[1] #set to that location (if there's multiple that start with configfile=, then it'll take the last one)
      print(f"\nSetting config file to {configFile}")
  #if we want to pass more arguments, we can specify them here

#set the multi config file
c = o.configparser.ConfigParser()
c.read(configFile)


#add the algos dir
sys.path.append(c['file locations']['algosDir'])

# posList = {} #init posList

#list of algorithms to be used and their corresponding stock lists to be bought (init with none)
algoList = c['allAlgos']['algoList'].split(',')
algoList = {e:[] for e in algoList}


#import all algos that are in algoList (they require an up-to-date posList, so must be imported after it's updated)
for algo in algoList:
  exec(f"import {algo}")

#used for coloring the displayed text
class bcolor:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


listsUpdatedToday = False


#TODO: at market close, show total p/l % for each algo
#TODO: add sentiment analysis to newsScrape
#TODO: add setting to each algo in config file to determine if it should sell before the end of the day or not (eg dj should, but fda shouldn't)
# https://www.investopedia.com/ask/answers/042115/whats-best-investing-strategy-have-during-recession.asp
#TODO: look at top gainers and analyze why they gain
def main(verbose=True):
  global algoList, posList, listsUpdatedToday
  portHist = a.getProfileHistory(str(dt.date.today()),'1M')['equity'] #get the closing prices of the portfolio over the last month
  portHist = [e for e in portHist if e is not None] #remove blank entries (using max on a list doesn't work if it contains a nonetype)
  maxPortVal=max(portHist) #get the max portfolio value over the last month
  cashMargin = float(c['account params']['cashMargin'])
  if(cashMargin<1): #cashMargin MUST BE GREATER THAN 1 in order for it to work correctly
    raise("Error: withdrawable funds margin is less than 1. Multiplier must be >=1")
  cash2hold = float(c['account params']['cash2hold'])
  acct = a.getAcct() #initialize the acct var
  
  #make sure we're still above the threshold to trade
  while float(acct['portfolio_value'])>=maxPortVal*float(c['account params']['portStopLoss']):
    
    acct = a.getAcct() #get account info
    pos = a.getPos() #get all held positions (no algo assigned)
    
    totalCash = float(acct['cash'])
    if(totalCash>=cash2hold*cashMargin): #if we have more buying power than the min plus some leeway, then reduce it to hold onto that buy pow
      # print(f"Can safely withdrawl ${round(cash2hold,2)}")
      totalCash = totalCash-cash2hold*cashMargin #subtract the cash2hold plus the margin
    elif(totalCash>cash2hold and totalCash<cash2hold*cashMargin):
      totalCash = 0 #stop trading if we've started to eat into the margin, that way we don't overshoot
      
    if(a.marketIsOpen()):
      print(f"\nPortfolio Value: ${acct['portfolio_value']}, total cash: ${totalCash}, {len(posList)} algos")
      #update the lists if not updated yet and that it's not currently updating
      if(not listsUpdatedToday and len([t.getName() for t in threading.enumerate() if t.getName().startswith('update')])==0):
        updateListsThread = threading.Thread(target=updateLists) #init the thread - note locking is required here
        updateListsThread.setName('updateLists') #set the name to the stock symb
        updateListsThread.start() #start the thread

      print("algo\tshares\tsymb \tcng frm buy\tcng frm cls\tnotes")
      print("----\t------\t-----\t-----------\t-----------\t-----")
      #look to sell things
      for algo in algoList:
        check2sell(algo,pos) #only look at the ones currently held
      
      if(a.timeTillClose()<60*float(c['time params']['buyTime']) and sum([t.getName().startswith('update') for t in threading.enumerate()])==0):
        #TODO: move cash adjustment from here to above
        tradableCash = totalCash if totalCash<float(c['account params']['cash2hold']) else max(totalCash-float(c['account params']['cash2hold'])*float(c['account params']['cashMargin']),0) #account for withholding a certain amount of cash+margin
        cashPerAlgo = tradableCash/len(algoList) #evenly split available cash across all algos
        #start buying things
        for e in algoList:
          buyThread = threading.Thread(target=check2buy, args=(e,cashPerAlgo, algoList[e])) #init the thread - note locking is required here
          buyThread.setName(e) #set the name to the stock symb
          buyThread.start() #start the thread
    
      time.sleep(60)
    
    else: #market is closed
      #update the max port val
      print("Updating max portfolio value... ", end="")
      portHist = a.getProfileHistory(str(dt.date.today()),'1M')['equity']
      portHist = [e for e in portHist if e is not None]
      maxPortVal=max(portHist)
      print(f"${maxPortVal}")

      syncPosList() #sync up posList to live data

      if(o.dt.date.today().weekday()==4 and o.dt.datetime.now().time()>o.dt.time(12)): #if it's friday afternoon
        #delete all csv files in stockDataDir
        print("Removing saved csv files")
        for f in glob(o.c['file locations']['stockDataDir']+"*.csv"):
          try: #placed inside a try statement in the event that the file is removed before being removed here
            o.os.unlink(f)
          except Exception:
            pass
        
      
      # clear all lists in algoList
      print("Clearing buyList")
      algoList = {e:[] for e in algoList}
      
      tto = a.timeTillOpen()
      print(f"Market opens in {round(tto/3600,2)} hours")
      #wait some time before the market opens      
      if(tto>60*float(c['time params']['updateLists'])):
        print(f"Updating stock lists in {round((tto-60*float(c['time params']['updateLists']))/3600,2)} hours")
        time.sleep(tto-60*float(c['time params']['updateLists']))
      #update stock lists
      print("Updating buyList")
      updateListsThread = threading.Thread(target=updateLists) #init the thread - note locking is required here
      updateListsThread.setName('updateLists') #set the name to the stock symb
      updateListsThread.start() #start the thread

      
      time.sleep(a.timeTillOpen())
      
  
  #TODO: in live version, this should be false
  a.sellAll(isManual=True) #if the portfolio value falls below our stop loss, automatically sell everything

#update all lists to be bought (this should be run as it's own thread)
def updateLists(verbose=False):
  global algoList, listsUpdatedToday
  
  #TODO: check that the buyfile is present and if it was updated today: if it was, then read directly from it, else generate lists
  errored = False
  if(verbose): print("Checking if buyList file is present")
  if(o.os.path.isfile(c['file locations']['buyList'])):
    if(verbose): print("File is present. Checking mod date")
    try:
      modDate = dt.datetime.strptime(time.strftime("%Y-%m-%d",time.localtime(os.stat(c['file locations']['buyList']).st_mtime)),"%Y-%m-%d").date() #if ANYONE knows of a better way to get the modified date into a date format, for the love of god please let me know
    except Exception:
      modDate = dt.date.today()-dt.timedelta(1)
    if(modDate==dt.date.today()):
      try:
        if(verbose): print("Reading from file")
        algoList = json.loads(open(c['file locations']['buyList'],'r').read())
      except Exception:
        if(verbose): print("invalid data in file")
        errored = True
    else:
      if(verbose): print(f"mod date not today - {modDate}")
      errored = True
  else:
    if(verbose): print("file does not exist")
    errored = True
  
  if(errored):
  
    lock = threading.Lock()
    revSplits = o.reverseSplitters()
    for e in algoList: #start a thread to update the list for each algorithm
      print(f"updating {e} list")
      updateThread = threading.Thread(target=updateList, args=(e,lock,revSplits)) #init the thread - note locking is required here
      updateThread.setName("update-"+e) #set the name to the stock symb
      updateThread.start() #start the thread
        
    #TODO: see the following because the updateList threads currently all access algoList, and the while loop is probably not the best solution
    # https://www.geeksforgeeks.org/multithreading-in-python-set-2-synchronization/
    while(len([t.getName() for t in threading.enumerate() if t.getName().startswith("update-")])>0):
      time.sleep(2)
    
    #save to a file
    if(verbose): print("Writing to buyList file")
    with open(c['file locations']['buyList'],'w') as f:
      f.write(json.dumps(algoList,indent=2))
  
  listsUpdatedToday = True

#update the to-buy list of the given algorithm, and exclude a list of rm stocks
def updateList(algo,lock,rm=[],verbose=False):
  global algoList
  if(verbose): print(f"Updating {algo} list")
  algoBuys = eval(algo+".getList()") #this is probably not safe, but best way I can think of
  algoBuys = [e for e in algoBuys if e not in rm] #remove any stocks that are in the rm list
  lock.acquire() #lock in order to write to the list
  algoList[algo] = algoBuys
  lock.release() #then unlock


#check to sell positions from a given algo (where algo is an aglo name, and pos is the output of a.getPos())
def check2sell(algo, pos):
  for e in pos:
    if(e['symbol'] in posList[algo] and posList[algo][e['symbol']]['sharesHeld']>0):
      #TODO: possibly getPrice with mktCap (and use in display), then if the number of shares held>mktCap/price, then sell the surplus
      print(f"{algo}\t\
            {round(float(posList[algo][e['symbol']]['sharesHeld']),2)}\t\
            {e['symbol']}\t\
            {bcolor.FAIL if round(float(e['unrealized_plpc'])+1,2)<1 else bcolor.OKGREEN}{round(float(e['unrealized_plpc'])+1,2)}{bcolor.ENDC}\t\t\
            {bcolor.FAIL if round(float(e['unrealized_intraday_plpc'])+1,2)<1 else bcolor.OKGREEN}{round(float(e['unrealized_intraday_plpc'])+1,2)}{bcolor.ENDC}\t\t\
            {posList[algo][e['symbol']]['note']}")

      if(posList[algo][e['symbol']]['shouldSell']): #if marked to sell, get rid of it immediately
        print(f"{e['symbol']} marked for immediate sale.")
        sell(e['symbol'],algo) #record and everything in the sell function
        
      else:
        goodSell = eval(f"{algo}.goodSell('{e['symbol']}')") #TODO: need to add shouldSell checking on held positions
        if(goodSell):
          if(f"{algo}-{e['symbol']}" not in [t.getName() for t in threading.enumerate()]): #make sure that the thread isn't already running
            #TODO: look at locking if need be
            triggerThread = threading.Thread(target=triggeredUp, args=(e['symbol'],algo)) #init the thread - note locking is required here
            triggerThread.setName(f"{algo}-{e['symbol']}") #set the name to the algo and stock symb
            triggerThread.start() #start the thread


#look to buy stocks from the stocks2buy list with the available funds for the algo
def check2buy(algo, cashAvailable, stocks2buy):
  global posList

  random.shuffle(stocks2buy) #shuffle the stocks2buy to avoid front loading
  #calculate the cash to be put towards various stocks in the algo (shouldn't be more than the cash available, but shouldn't be less than than the minDolPerStock (unless mindol > cashAvail))
  cashPerStock = min(cashAvailable,max(float(c['account params']['minDolPerStock']),cashAvailable/len(stocks2buy)))
  
  #TODO: add comments to justify why we're doing what we're doing
  #TODO: Also other printing should happen rather than printing the actual response
  #TODO: also, this should probably loop forever/until a certain condition is met, and also needs to check that a stock isn't already trying to sell, and that this thread isn't already running

  #loop through the stocks to be bought
  for stock in stocks2buy:
    
    #populate the information about the stock (either from the posList if it's present, else with default info)
    stockInfo = posList[algo][stock] if stock in posList[algo] else {
          "sharesHeld":0,
          "lastTradeDate":"NA",
          "lastTradeType":"NA",
          "buyPrice":0,
          "shouldSell":False,
          "note":""
        }
    
    #get the last date it was traded
    try:
      lastTradeDate = dt.datetime.strptime(stockInfo[algo][stock]['lastTradeDate'],"%Y-%m-%d").date()
    except Exception:
      lastTradeDate = dt.date.today()-dt.timedelta(1) #if it isn't populated, just set it to yesterday
    
    
    if lastTradeDate < dt.date.today() or stockInfo['lastTradeType']!="sell":
      
      [buyPrice,mktCap] = a.getPrice(stock,withCap=True) #get the appx price to buy at, and the marketcap (to calculate the most shares we'll be allowed to purchase)
      shares = int(min(cashPerStock/buyPrice,mktCap*float(c['account param']['maxVolPerc']))) #
      if(shares>0):
        buy(int(cashPerStock/a.getPrice(stock)),stock,algo,buyPrice)
    
#a stock has reached a trigger point and should begin to be checked more often (it will be sold in this function)
def triggeredUp(stock, algo):
  maxPrice = 0
  curPrice = 0
  sellUpDn = float(eval(algo+".sellUpDn()"))
  while(curPrice>=sellUpDn*maxPrice and a.timeTillClose()>30):
    curPrice = a.getPrice(stock)
    maxPrice = max(maxPrice,curPrice)
    print(f"{algo}\t{stock}\t{round(curPrice/maxPrice,2)} : {round(sellUpDn,2)}")
    time.sleep(3) #slow it down a little bit
  sell(stock, algo)


#basically just a market order for the stock and then record it into an order info file
def sell(stock, algo):
  global posList #TODO: may need to incorporate locking
  if(posList[algo][stock]['sharesHeld']>0):
    r = a.createOrder("sell",float(posList[algo][stock]['sharesHeld']),stock)
  else:
    print(f"No shares held of {stock}")
    return False
  if(r['status'] == "accepted"): #check that it actually sold
    posList[algo][stock] = { #update the entry in posList
        "sharesHeld":0,
        "lastTradeDate":str(dt.date.today()),
        "lastTradeType":"sell",
        "buyPrice":0,
        "shouldSell":False,
        "note":""
      }
    open(c['file locations']['posList'],'w').write(json.dumps(posList,indent=2)) #update the posList file
    return True
  else:
    print(f"Order to buy {shares} shares of {stock} not accepted")
    return False

#basically just a market buy of this many shares of this stock for this algo
def buy(shares, stock, algo, buyPrice):
  r = a.createOrder("buy",shares,stock) #this needs to happen first so that it can be as accurate as possible
  global posList #TODO: may need to incorporate locking

  if(r['status'] == "accepted"): #check to make sure that it actually bought
    posList[algo][stock] = { #update the entry in posList
        "sharesHeld":float(posList[algo][stock]['sharesHeld'])+float(r['qty']) if stock in posList[algo] else float(r['qty']),
        "lastTradeDate":str(dt.date.today()),
        "lastTradeType":"buy",
        #running avg = (prevAvg*n+newVals)/(n+m)
        "buyPrice":(posList[algo][stock]['buyPrice']*posList[algo][stock]['sharesHeld']+buyPrice)/(posList[algo][stock]['sharesHeld']+float(r['qty'])) if stock in posList[algo] else buyPrice,
        "shouldSell":False,
        "note":""
      }
    open(c['file locations']['posList'],'w').write(json.dumps(posList,indent=2)) #update posList file
    
    return True
  else: #it didn't actually buy
    print(f"Order to buy {shares} shares of {stock} not accepted")
    return False


#set up the position list and do some error checking to make sure it's correct (take list of algos as arg in the event the pos list needs to be populated)
def setPosList(algoList, verbose=True):
  posList={}
  #if the posList file doesn't exist
  if(not os.path.isfile(c['file locations']['posList'])):
    if(verbose): print("File is missing. Creating and adding blank lists...")
    with open(c['file locations']['posList'],'w') as f:
      f.write(json.dumps({e:{} for e in algoList}))
    posList = json.loads(open(c['file locations']['posList'],'r').read())
  else: #if it does exist
    try: #try reading any json data from it
      with open(c['file locations']['posList'],'r') as f:
        posList = json.loads(f.read())
      
      missingAlgos = [algo for algo in algoList if algo not in posList]
      if(verbose): print("" if len(missingAlgos)==0 else f"Adding {len(missingAlgos)} algo{'s' if len(missingAlgos)>1 else ''} to posList")
      for algo in missingAlgos:
        posList[algo] = {}
        
      #write the missing algos to the file
      with open(c['file locations']['posList'],'w') as f:
        f.write(json.dumps(posList))
        
    except Exception: #if it fails, then just write the empty algoList to the file
      #TODO: this is dangerous! This could potentially overwrite all saved position data if there's any error above. Make this more robust
      if(verbose): print("Something went wrong. Overwriting file")
      with open(c['file locations']['posList'],'w') as f:
        f.write(json.dumps({e:{} for e in algoList}))
      posList = json.loads(open(c['file locations']['posList'],'r').read())

  return posList



#sync what we have recorded and what's actually going on in the account
def syncPosList(verbose=False):
  global posList
  print("Syncing posList...")
  
  if(verbose): print("getting actually held positions")
  p = a.getPos()
  heldPos = {e['symbol']:float(e['qty']) for e in p} #actually held positions
  heldBuyPrices = {e['symbol']:float(e['avg_entry_price']) for e in p} #TODO: combine this into heldPos and either rework recPos or change some conditionals to account for the addition


  if(verbose): print("Adding any missing fields to current records")
  for algo in posList:
    for symb in posList[algo]:
      if('sharesHeld' not in posList[algo][symb]):
        if(verbose): print(f"{algo} {symb} missing sharesHeld")
        posList[algo][symb]['sharesHeld'] = 0
      if('lastTradeDate' not in posList[algo][symb]):
        if(verbose): print(f"{algo} {symb} missing lastTradeDate")
        posList[algo][symb]['lastTradeDate'] = "NA"
      if('lastTradeType' not in posList[algo][symb]):
        if(verbose): print(f"{algo} {symb} missing lastTradeType")
        posList[algo][symb]['lastTradeType'] = "NA"
      if('buyPrice' not in posList[algo][symb]):
        if(verbose): print(f"{algo} {symb} missing buyPrice")
        posList[algo][symb]['buyPrice'] = heldBuyPrices[symb] if symb in heldBuyPrices else 0
      if('shouldSell' not in posList[algo][symb]):
        if(verbose): print(f"{algo} {symb} missing shouldSell")
        posList[algo][symb]['shouldSell'] = False
      if('note' not in posList[algo][symb]):
        if(verbose): print(f"{algo} {symb} missing note")
        posList[algo][symb]['note'] = ""
  
  
  #total stocks in posList
  if(verbose): print("getting recorded positions...")
  recPos = {} #recorded positions
  for algo in posList: #for every algo in the posList
    if(len(posList)>0):
      for stock in posList[algo]: #for every stock in that algo
        if stock not in recPos: #if that stock isn't already in the recorded positions
          recPos[stock] = float(posList[algo][stock]['sharesHeld']) #add it
        else: #if it already is
          
          #ensure that all fields are present
          if(verbose): print(f"Ensuring correct data for {stock}")
          if('sharesHeld' not in posList[algo][stock]):
            if(verbose): print("Missing sharesHeld")
            posList[algo][stock]['sharesHeld'] = 0
          if('lastTradeDate' not in posList[algo][stock]):
            if(verbose): print("Missing lastTradeDate")
            posList[algo][stock]['lastTradeDate'] = str(dt.date.today()-dt.timedelta(1))
          if('lastTradeType' not in posList[algo][stock]):
            if(verbose): print("Missing lastTradeType")
            posList[algo][stock]['lastTradeType'] = 'NA'
          if('shouldSell' not in posList[algo][stock]):
            if(verbose): print("Missing shouldSell")
            posList[algo][stock]['shouldSell'] = False
          if('buyPrice' not in posList[algo][stock]):
            if(verbose): print("Missing buyPrice")
            posList[algo][stock]['buyPrice'] = 0
          
          
          
          recPos[stock] += float(posList[algo][stock]['sharesHeld']) #add the shares held


  if(not eq(recPos,heldPos)):
    if(verbose): print("discrepency found between records and actuals")
    #if there are any stocks recorded that aren't in the heldPos, remove them
    #if there are an excess of shares in the recPos than the heldPos, look for any in the algos that match the disparity, and remove them from that algo
      #if none match (i.e. heldPos and recPos both have a stock, but there's an unknown amount extra in recPos), then just sell it all
  
    #if there are any stocks in heldPos that aren't recorded, then compare to algoList
      #if it's in algolist, assign to all algos that have it, else assign to algo with the smallest gain to offload it asap
    #if there are an excess of shares in the heldPos than the recPos, then add the excess to the algo with the highest gain to increase gains as much as possible

    #compare recPos to heldPos

    #if there are any stocks recorded that aren't in the heldPos, remove them
    for symb in [s for s in recPos if s not in heldPos]: #for all stocks in recorded and not in heldPos
      for algo in posList: #check every algo
        if(verbose): print(f"{symb} not found in actuals. Removing from {algo} records")
        posList[algo].pop(symb,None) #remove from posList
      recPos.pop(symb,None) #remove from recorded
    
    #for each stock, if there are an excess of shares in the recPos than the heldPos, look for any in the algos that match the disparity, and remove them from that algo
      #if none match (i.e. heldPos and recPos both have a stock, but there's an unknown amount extra in recPos), then trim off the amount extra from the algo that has the most above the disparity
        #if no algo has any above it: then sell the whole lot TODO: this should probably be handled differently, but it's some complexity that can be saved for later
    for symb in [s for s in recPos if recPos[s]>heldPos[s]]: #for all stocks where the recorded is greater than the held
      for algo in posList: #for every algo
        #remove any that may be exact matches
        if float(posList[algo][symb]['sharesHeld'])==recPos[symb]-heldPos[symb]:
          if(verbose): print(f"Removing {float(posList[algo][symb]['sharesHeld'])} shares of {symb} from {algo} records")
          recPos[symb] -= float(posList[algo][symb]['sharesHeld'])
          if(recPos[symb]==0):
            recPos.pop(symb,None)
          posList[algo].pop(symb,None)
     
      #if there's still a discrepency (ie. there is not an exact difference)
      if(recPos[symb]>heldPos[symb]): #if the recorded still has more than the held
        #get algos with the symbol and the number of shares of that symbol
        if(verbose): print(f"more shares of {symb} in records than actuals")
        algosWithStock = {e:float(posList[e][symb]['sharesHeld']) for e in posList if symb in posList[e]} #get the number of shares per algo if the algo has the stock
        for algo in algosWithStock:
          #TODO: this should probably be changed to spread out over multiple algos rather than just 1
          if(algosWithStock[algo]>=recPos[symb]-heldPos[symb]): #if an algo has more than the disparity
            if(verbose): print(f"{algo} has {algosWithStock[algo]} shares of {symb}. Removing {recPos[symb]-heldPos[symb]} shares")
            posList[algo][symb]['sharesHeld'] -= recPos[symb]-heldPos[symb] #remove the disparity
            recPos[symb] -= recPos[symb]-heldPos[symb]
            break

        #TODO: this needs to be in a loop around every algo. currently algo is not defined below
        if(recPos[symb]>heldPos[symb]): #if the disparity wasn't caught, then just sell the lot
          print(f"Could not find a suitable sync for {symb}. Selling the lot.")
          sell(symb, algo)



    #compare heldPos to recPos

    #ensure algoList is up to date
  if(not eq(recPos, heldPos)): #compare again after the initial comparison
    if(not listsUpdatedToday and len([t for t in threading.enumerate() if t.getName().startswith('update')])==0):
      updateListsThread = threading.Thread(target=updateLists) #init the thread - note locking is required here
      updateListsThread.setName('updateLists') #set the name to the stock symb
      updateListsThread.start() #start the thread

    if(verbose): print("Waiting for stock lists to finish updating...")
    while(not listsUpdatedToday or len([t for t in threading.enumerate() if t.getName().startswith('update')])>0): #wait for the lists to finish updating
      # print([t.getName() for t in threading.enumerate() if t.getName().startswith('update')])
      time.sleep(2)
    if(verbose): print("lists done updating")

    #check that symb is somewhere in algoList
    #if it is, then add it to the algo that has it with the highest gain
    #else append it to the algo with the smallest gain
    for symb in [s for s in heldPos if s not in recPos]: #for all stocks actually held and not recorded

      algosWithStock = [e for e in algoList if symb in algoList[e]] #try and find a home for a stock by looking in the stocks to be bought (get all algos that may have it)
      if(len(algosWithStock)>0): #if an algo has it
        maxAlgo = ['x',0] #algo and the max gain of the stock
        #get the algo with the max gain for this stock
        for algo in algosWithStock: #look thru each algo that could hold the stock
          sellUp = eval(f"{algo}.sellUp('{symb}')") #find the sell up of that algo
          maxAlgo = [algo,sellUp] if sellUp>maxAlgo[1] else maxAlgo #get the greater of the two algos
        if(verbose): print(f"Adding {heldPos[symb]} shares of {symb} to {maxAlgo[0]}.")
        posList[maxAlgo[0]][symb] = {'lastTradeDate':'NA',
                                     'lastTradeType':'NA',
                                     'sharesHeld':heldPos[symb],
                                     'shouldSell':False,
                                     'buyPrice':heldBuyPrices[symb],
                                     'note':''
                                    }
        recPos[symb]=heldPos[symb] #also add the stock to the recPos temp var
        
      else: #if no algo has it
        minAlgo = ['x',100000] #algo and the min gain of the stock
        for algo in algoList: #for every algo that'll potentially gain
          sellDn = eval(f"{algo}.sellDn('{symb}')") #get the sell dn of each algo
          #TODO: figure out the logic here if it shoud be < or >, and what we value more (least loss, or highest variance)
          minAlgo = [algo,sellDn] if sellDn<minAlgo[1] else minAlgo #get the greater of the the two algos
        #add to the algo with the least loss (to minimize risk)
        if(verbose): print(f"No algo found to have {symb}. Adding {heldPos[symb]} shares to {minAlgo[0]}.")
        posList[minAlgo[0]][symb] = {'lastTradeDate':'NA',
                                     'lastTradeType':'NA',
                                     'sharesHeld':heldPos[symb],
                                     'buyPrice':heldBuyPrices[symb],
                                     'shouldSell':False,
                                     'note':''
                                    }
        recPos[symb]=heldPos[symb] #also add the stock to the recPos temp var

    #find symbols that have more actual shares than recorded shares
    #add the shares to the algo with the highest gain
    for symb in [s for s in heldPos if heldPos[s]>recPos[s]]: #for all stocks where the actual is greater than the recorded
      maxAlgo = list(posList)[0] #init to the first algo
      for algo in posList: #get the algo with the max gain potential
        if(symb in posList[algo]): #ensure that the symbol is in the algo (TODO: this could potentially get put into the for loop in the prev line?)
          maxAlgo = algo if eval(f"{algo}.sellUp(symb)")>eval(f"{maxAlgo}.sellUp('{symb}')") else maxAlgo
      
      posList[maxAlgo][symb]['sharesHeld'] += heldPos[symb]-recPos[symb] #add in the disparity
      
  #TODO: figure out why it's adding blanks in the first place?? Where are they even coming from??
  if(verbose): print("Removing blanks")
  for algo in posList:
    for symb in list(posList[algo]): #must be cast as list in order to not change dict size (this makes a copy)
      if(posList[algo][symb]['sharesHeld']==0):
        posList[algo].pop(symb,None)

  
  if(verbose): print("Marking to be sold")
  revSplits = o.reverseSplitters()
  for algo in posList:
    for symb in posList[algo]:
      if(symb in revSplits):
        if(verbose): print(f"{algo} - {symb} marked for sale")
        posList[algo][symb]['shouldSell'] = True
  
  
  #write to the file
  with open(c['file locations']['posList'],'w') as f:
    if(verbose): print("Writing to posList file")
    f.write(json.dumps(posList,indent=2))
  
  print("Done syncing posList")



#run the main function
if __name__ == '__main__':
  global posList
  print("\nStarting up...\n")
  a.checkValidKeys()
  
  if(len(a.getPos())==0): #if the trader doesn't have any stocks (i.e. they've not used this algo yet), then give them a little more info
    print("Will start buying "+str(c['time params']['buyTime'])+" minutes before next close")
  
  posList = setPosList(algoList) #initiate/populate the list of positions by algo
  
  #init the algos
  for algo in algoList:
    exec(f"{algo}.init('{configFile}')")
  
  syncPosList() #in the event that something changed during the last run, this should catch it
    
  main() #start running the program
