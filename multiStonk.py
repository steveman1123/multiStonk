#Steven Williams (2021)
#Stock trading program to use multiple algorithms/strategies as defined in the config file and present in the algos directory to perform low frequency shortterm trades

print("\nStarting up...")

verbose=False

#install any missing packages
# print("Checking for missing packages")
from pip._internal.operations import freeze
#get installed pkgs
installedpkgs = [e.split('==')[0].lower() for e in freeze.freeze()]
if(verbose): print('installed',installedpkgs)
#get required pkgs
pkgs = open("./req.txt",'r').read().split("\n")
#remove blank lines and comments
pkgs = [e.lower() for e in pkgs if len(e)>0 and not e.startswith("#")]
if(verbose): print('required',pkgs)
#compare
neededpkgs = [e for e in pkgs if e not in installedpkgs]
if(verbose): print('needed',neededpkgs)
#install any missing ones
for e in neededpkgs:
  print("installing",e)
  pip.main(['install',e])



import ndaqfxns as n
import alpacafxns as a
import random, time, json, sys, os, traceback
import datetime as dt
from glob import glob
from operator import eq
from colorama import init as colorinit

colorinit() #allow coloring in Windows terminals

#TODO: should add the ability to store a global unsorted list that multiple algos pull from (eg define a price and vol range, then pass that to every algo that requests it)

#TODO: add check that if the number of shares held of stock to buy is > some % of the avg # of shares held/stock, then don't buy more
# ^ this is to prevent buying a bunch of really cheap ones when cash is low
#TODO: when removing an algo, have the cash from that algo moved proportionally to where the stocks are moved to (so if there's 25 stocks and $100 that need to be moved, then for each stock that moved $4 should also be moved to the new algo (proportionally for invested and returned amounts)

#TODO: fix algo ROI calculations - they are very wrong
#TODO: display how many stocks are unable to be sold at the end of every day (or every minute?)
#TODO: if the change from buy or change from sell is > than some limit (like 4.0), then sell immediately (usually means reverse split)


#init the api key file var
keyfile = None

#parse args and get the config file
configFile="./configs/multi.config"
if(len(sys.argv)>1): #if there's an argument present
  for arg in sys.argv[1:]:
    if(arg.lower() in ['-h','--help']): #if there's an argument regarding the config file
      print(("\n"
             "Stockbot\n"
            "Uses multiple algorithms to trade stocks based on the functions specified in the config file and present in the algos directory. Intended to run in the terminal 24/7\n\n"
            "Syntax:\n"
            "[ -h/--help | path/to/file.config | keyfile=path/to/keyfile.txt ]\n"
            "-h\t: displays this help menu\n"
            "configfile\t: point to the config file containing all settings required to run the program (defaults to "+configFile+")\n"
            "keyfile\t: point to the file containing the api keys. Defaults to the file specified in the config file.\n"
            "example: python3 ./multiStonk.py keyfile=../stockStuff/apikeys/keys.txt configfile=configs/multi.config\n"
            "\n"
            "report any errors to https://github.com/steveman1123\n"
            ))
      exit()

    #check for a keyfile
    elif(arg.lower().startswith("keyfile=")):
      keyfile = arg.split("=")[1]
    #check that the arg is a valid config file
    elif(arg.lower().startswith("configfile=")):
      configFile = arg.split("=")[1]
    #if we want to pass more arguments, we can specify them here (also make sure to include them in the help menu)
    else:
      raise ValueError("Invalid argument. Make sure config file is present or use '-h'/'--help' for help.")


#set the multi config file
c = n.configparser.ConfigParser()
c.read(configFile)


#if no keyfile is specified in args, use default
if(keyfile is None):
  keyfile = c['file locations']['keyFile']

#list of algorithms to be used and their corresponding stock lists to be bought (init with none)
algoList = c['allAlgos']['algoList'].replace(" ","").split(',') #var comes in as a string, remove spaces, and turn into comma separated list
algoList = {e:{} for e in algoList}

#tell the user general setting information
print(f"Config file\t{configFile}")
print(f"Key file \t{keyfile}")
print(f"posList file\t{c['file locations']['posList']}")
print(f"buyList file\t{c['file locations']['buyList']}")
print(f"Error log \t{c['file locations']['errLog']}")
print("Using the algos: ",", ".join(list(algoList)),end="\n\n")

#init the alpaca functions
a.init(keyfile,int(c['account params']['isPaper']))

#add the algos dir
sys.path.append(c['file locations']['stockAlgosDir'])

#import all algos that are in algoList (they require an up-to-date posList, so must be imported after it's updated)
for algo in algoList: exec(f"import {algo}")


#change display text color
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


#init some gobal vars
listsUpdatedToday = False #tell everyone whether the list has been updated yet today or not
closeTime = n.closeTime() #get the time in datetime format of when the market closes (reference this when looking at time till close)

minCashMargin = float(c['account params']['minCashMargin']) #extra cash to hold above hold value
if(minCashMargin<1): #minCashMargin MUST BE GREATER THAN 1 in order for it to work correctly
  raise ValueError("Error: cash margin is less than 1. Multiplier must be >=1")
minCash2hold = float(c['account params']['minCash2hold'])
maxCash2hold = float(c['account params']['maxCash2hold'])
#set the max number of times to try selling a stock (sometimes a stock get sstuck in an unsellable state and alpaca returns a 403 error)
maxAttempts = int(c['account params']['maxAttempts'])

#main function to run continuously
def main(verbose=False):
  #values to be used across functions and are edited here
  global algoList, posList, listsUpdatedToday, closeTime, cashList, triggeredStocks
  
  ###
  #initiate settings, algorithms, variables and ensure proper configuration
  ###
  #should contain elements of format algo|stock of the stocks that have triggered up
  triggeredStocks = set() 
  ask2sell = True #if this is true, then the program will ask to sell all if portval drops below some % of maxPortVal
  a.checkValidKeys(int(c['account params']['isPaper'])) #check that the keys being used are valid
  #if the trader doesn't have any stocks (i.e. they've not used this algo yet), then give them a little more info
  if(len(a.getPos())==0): print(f"Will start buying {c['time params']['buyTime']} minutes before next close")
  
  #initiate/populate the list of positions by algo
  [posList,cashList] = setPosList(algoList)


  if(verbose):
    print("posList:",posList)
    print("cashList:",cashList)


  #init the algos
  for algo in algoList:
    exec(f"{algo}.init('{configFile}')")
  updateLists()
  
  syncPosList() #in the event that something changed during the last run, this should catch it
  print("\n") #leave a space between startup and main sequence
    
  if(verbose): print(json.dumps(algoList,indent=2))

  ###
  #initiate settings related to the account parameters
  ###
  portHistM = a.getProfileHistory(str(dt.date.today()),'1M')
  maxPortVal = sorted(portHistM.items(), key=lambda x: x[1]['eq'])[-1][1]['eq']
  
  isManualSellOff = not int(c['account params']['portAutoSellOff'])
  
  if(verbose):
    print("max portfolio value of last month:",maxPortVal)
    print("manually close all positions?",isManualSellOff)

  ###
  #part to run forever (unless cancelled or an unexpected error occurs)
  ###
  while True:
    
    ###
    #get current account statuses
    ###
    acct = a.getAcct() #get account info
    pos = a.getPos() #get all held positions (no algo assigned)
    
    
    ###
    #ensure we're still above the threshold to trade (if not, see if we should ask to sell, and if we have anything to be sold in the first place)
    ###
    if(ask2sell and float(acct['portfolio_value'])<maxPortVal*float(c['account params']['portStopLoss']) and len(pos)>0):
      print(f"Portfolio value of ${acct['portfolio_value']} is less than {c['account params']['portStopLoss']} times the max portfolio value of ${maxPortVal}.")
      if(not isManualSellOff): print("Automatically selling all...")
      soldAll = a.closeAll(isManual=isManualSellOff) #if the portfolio value falls below our stop loss, automatically sell everything
      if(soldAll): break #stop the program if the selling occured
      if(isManualSellOff): #if the selling is set to manual, then ask if the user wants to keep being asked to sell all or not
        ask2sell = (input("Ask to sell all again today (y/n)? ").lower())!="n"
        if(ask2sell):
          print("Will continue asking to sell all today")
        else:
          print("Will ask to sell all again tomorrow")
      
    ###
    #calculate tradable cash
    ###
    totalCash = float(acct['cash'])
    tradableCash = getTradableCash(totalCash, maxPortVal)
      
    ###
    #execute when the market is open
    ###
    if(n.marketIsOpen()):
      print(f"\nPortfolio Value: ${acct['portfolio_value']}, total cash: ${round(totalCash,2)}, tradable cash: ${round(tradableCash,2)}, port stop loss: {round(maxPortVal*float(c['account params']['portStopLoss']),2)},  {len(posList)} algos | {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

      #update the lists if not updated yet and that it's not currently updating
      if(not listsUpdatedToday and len([t.name for t in n.threading.enumerate() if t.name.startswith('update')])==0):
        updateListsThread = n.threading.Thread(target=updateLists) #init the thread - note locking is required here
        updateListsThread.name = 'updateLists' #set the name to the stock symb
        updateListsThread.start() #start the thread

      
      #look to sell things
      check2sells(pos)
      
      #start checking to buy things if within the buy time frame and lists are not being updated

      if(verbose): 
        print("current threads:",[t for t in n.threading.enumerate()])
        print(f"ttc=",n.timeTillClose())

      if(n.timeTillClose()<=60*float(c['time params']['buyTime']) and sum([t.name.startswith('update') for t in n.threading.enumerate()])==0):
        tradableCash = getTradableCash(totalCash, maxPortVal) #account for withholding a certain amount of cash+margin
        cashPerAlgo = tradableCash/len(algoList) #evenly split available cash across all algos
        #start buying things
        #print(tradableCash,cashPerAlgo,algoList,sep="\n")
        for algo in algoList:
          if(verbose): print(f"starting buy thread {algo}")
          buyThread = n.threading.Thread(target=check2buy, args=(algo,cashPerAlgo, list(algoList[algo]),False)) #init the thread
          buyThread.name = algo #set the name to the algo
          buyThread.start() #start the thread
    
      time.sleep(60)
    
    
    
    ###
    #execute when the market is closed
    ###
    else:
      ###
      #execute immediately after close
      ###
      print(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"market closed\n")
      
      '''
      #TODO: these numbers are incorrect for some reason. check math
      #display the total p/l % of each algo
      print("Algo ROI estimates:")
      for algo in posList:
        #get all postions
        pos = a.getPos()
        #get the current prices of all the stocks in a given algo
        curPrices = [float(e['current_price']) for e in pos if e['symbol'] in posList[algo]]
        
        #get the equity invested in the algo (shes*price of share)
        algoEqVal = sum([posList[algo][s]['sharesHeld']*curPrices[s.upper()] for s in posList[algo] if s.upper() in curPrices])
        #get the cash earned by the algo
        algoCashVal = cashList[algo]['earned']

        #current value is equity+cash dedicated to algo
        algoCurVal = algoEqVal+algoCashVal

        if(verbose): print(algo,"current val:",algoCurVal)
        
        #update the invested amount and set the buyVal var
        if(cashList[algo]['invested']==0):
          cashList[algo]['invested'] = sum([posList[algo][s]['sharesHeld']*posList[algo][s]['buyPrice'] for s in posList[algo]])
        algoBuyVal = cashList[algo]['invested']

        if(verbose): print(algo,"invested val:",algoBuyVal)

        #make sure that we don't div0 if the list is empty
        if(algoBuyVal>0):
          roi = round(algoCurVal/algoBuyVal,2)
        #if the buyVal is 0, then that means either no info or no stocks held, so it's nearly impossible to make a judgement
        else:
          roi = 1
        
        print(f"{algo} - {bcolor.FAIL if roi<1 else bcolor.OKGREEN}{roi}{bcolor.ENDC}") #display the ROI
      '''

      #get the histories to calculate max port val and ROI
      portHistM = a.getProfileHistory(str(dt.date.today()),'1M')
      portHistY = a.getProfileHistory(str(dt.date.today()),'1A')
      #get the max port val from the last month
      maxPortInf = sorted(portHistM.items(), key=lambda x: x[1]['eq'])[-1]
      maxPortVal = maxPortInf[1]['eq']
      maxPortValDate = maxPortInf[0]
      #get the current portfolio value
      curPortVal = portHistM[max(list(portHistM.keys()))]['eq']

      if(portHistM[min(list(portHistM))]['eq'] != 0):
        mroi = portHistM[max(list(portHistM))]['eq']/portHistM[min(list(portHistM))]['eq']
      else:
        mroi = 1
      if(portHistY[min(list(portHistY))]['eq'] != 0):
        yroi = portHistY[max(list(portHistY))]['eq']/portHistY[min(list(portHistY))]['eq']
      else:
        yroi = 1

      print("1 Month ROI:",bcolor.FAIL if mroi<1 else bcolor.OKGREEN,round(mroi,3),bcolor.ENDC)
      print("1 Year ROI:",bcolor.FAIL if yroi<1 else bcolor.OKGREEN,round(yroi,3),bcolor.ENDC)

      
      #display max val and date
      print(f"\nHighest portVal in the last month: ${round(maxPortVal,2)} on {maxPortValDate}")
      print(f"Current portVal: ${round(curPortVal,2)} ({round(100*curPortVal/maxPortVal,3)}% of highest)")
      print(f"Port stop-loss: ${round(float(c['account params']['portStopLoss'])*maxPortVal,2)} ({round(100*float(c['account params']['portStopLoss']),2)}% of highest)\n")
      syncPosList() #sync up posList to live data
      
      # clear all lists in algoList
      print("Clearing buyList")
      algoList = {e:{} for e in algoList}
      
      #reset ask2sell in order to ask again tomorrow
      ask2sell = True
      
      tto = a.timeTillOpen()
      print(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
      print(f"Market opens in {round(tto/3600,2)} hours")
      #wait some time before the market opens      
      if(tto>60*float(c['time params']['updateLists'])):
        print(f"Updating stock lists in {round((tto-60*float(c['time params']['updateLists']))/3600,2)} hours\n")
        time.sleep(tto-60*float(c['time params']['updateLists']))
      
      
      ###
      #execute some time before the market opens
      ###
      #update stock lists
      print(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"Updating buyList") #TODO: move this into the thread or within the thread have a "done updating buylist"
      updateListsThread = n.threading.Thread(target=updateLists) #init the thread - note locking is required here
      updateListsThread.name = 'updateLists' #set the name to the stock symb
      updateListsThread.start() #start the thread

      closeTime = n.closeTime() #get the next closing time
      #wait until market is open is open before continuing
      #plus a few seconds since it's been having issues jumping the gun just before the market opens
      #TODO: not sure if this will work as of 2023-07-31. Wait and see
      time.sleep(a.timeTillOpen()+30)
      
      

#given the total cash and cash parameters, return the tradable cash
def getTradableCash(totalCash, maxPortVal,verbose=False):
  if(totalCash<minCash2hold): #0-999
    if(verbose): print(1)
    if(verbose): print(totalCash)
    return totalCash
  elif(minCash2hold<=totalCash<=minCash2hold*minCashMargin): #1000-1100
    if(verbose): print(2)
    if(verbose): print(0)
    return 0
  elif(minCash2hold*minCashMargin<totalCash<maxPortVal*maxCash2hold): #1101-.25*max
    if(verbose): print(3)
    if(verbose): print(totalCash-minCash2hold*minCashMargin)
    return totalCash-minCash2hold*minCashMargin
  else: #.25*max-inf
    if(verbose): print(4)
    if(verbose): print(maxPortVal*maxCash2hold,minCash2hold*minCashMargin)
    return totalCash-max(maxPortVal*maxCash2hold,minCash2hold*minCashMargin)


#update all lists to be bought (this should be run as it's own thread)
def updateLists(verbose=False):
  global algoList, listsUpdatedToday
  print(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

  #check that the buyfile is present and if it was updated today: if it was, then read directly from it, else generate lists
  errored = False
  if(verbose): print("Checking if buyList file is present")
  if(n.os.path.isfile(c['file locations']['buyList'])):
    if(verbose): print("File is present. Checking mod date")
    try:
      modDate = dt.datetime.strptime(time.strftime("%Y-%m-%d",time.localtime(os.stat(c['file locations']['buyList']).st_mtime)),"%Y-%m-%d").date() #if ANYONE knows of a better way to get the modified date into a date format, for the love of god please let me know
    except Exception:
      modDate = dt.date.today()-dt.timedelta(1)
    if(modDate==dt.date.today()):
      try:
        if(verbose): print("Reading from file")
        f = json.loads(open(c['file locations']['buyList'],'r').read())
        if(len([e for e in f if e not in algoList])>0 or len([e for e in algoList if e not in f])>0):
          if(verbose): print("mismatch between saved buy list and algos being used")
          errored = True
        else:
          algoList = f #valid file, valid data, so should just read from the file
      except Exception:
        if(verbose): print("invalid data in file")
        errored = True
    else:
      if(verbose): print(f"mod date not today - {modDate}")
      errored = True
  else:
    if(verbose): print("file does not exist")
    errored = True
  #TODO: check that all algos in the algolist are present in the buy list as well (in the event that an algo has been added or removed after updating today
  if(errored):
  
    lock = n.threading.Lock()
    revSplits = n.reverseSplitters()
    for e in algoList: #start a thread to update the list for each algorithm
      # print(f"updating {e} list")
      updateThread = n.threading.Thread(target=updateList, args=(e,lock,revSplits)) #init the thread - note locking is required here
      updateThread.name = "update-"+e #set the name to the stock symb
      updateThread.start() #start the thread
        
    #TODO: see the following because the updateList threads currently all access algoList, and the while loop is probably not the best solution for waiting
    # https://www.geeksforgeeks.org/multin.threading-in-python-set-2-synchronization/
    #wait for the threads to finish updating, or the exitFlag is triggered
    while(len([t.name for t in n.threading.enumerate() if t.name.startswith("update-")])>0 and not exitFlag):
      time.sleep(2)
    
    if(not exitFlag):
      #save to a file
      if(verbose): print("Writing to buyList file")
      with open(c['file locations']['buyList'],'w') as f:
        f.write(json.dumps(algoList,indent=2))
  
  listsUpdatedToday = True

#update the to-buy list of the given algorithm, and exclude a list of rm stocks
def updateList(algo,lock,rm=[],verbose=False):
  global algoList
  if(not exitFlag): #ensure that the exit flag isn't set
    if(verbose): print(f"Updating {algo} list")
    #TODO: exitFlag doesn't stop individual getList()'s. Might not be a bad idea to read it somehow?
    algoBuys = eval(algo+".getList()") #this is probably not safe, but best way I can think of
    algoBuys = {e:algoBuys[e] for e in algoBuys if e not in rm} #remove any stocks that are in the rm list
    lock.acquire() #lock in order to write to the list
    algoList[algo] = algoBuys
    lock.release() #then unlock



#TODO: check2buy should run more continuously/should be it's own thread (rather than a single loop through, it should repeat until cash is spent per algo) <- this might already be addressed?
#look to buy stocks from the stocks2buy list with the available funds for the algo
def check2buy(algo, cashAvailable, stocks2buy, verbose=False):
  global posList, cashList
  if(verbose): print(stocks2buy)
  random.shuffle(stocks2buy) #shuffle the stocks2buy to avoid front loading
  #calculate the cash to be put towards various stocks in the algo (shouldn't be more than the cash available, but shouldn't be less than than the minDolPerStock (unless mindol > cashAvail))
  if(len(stocks2buy)>0):
    cashPerStock = min(cashAvailable,max(float(c['account params']['minDolPerStock']),cashAvailable/len(stocks2buy)))
    if(verbose): print(f"stocks to buy for {algo}: {len(stocks2buy)}\tcash available for {algo}: {round(cashAvailable,2)}\tcash per stock: {round(cashPerStock,2)}")
  else:
    print(f"No stocks to buy for {algo}")
  #loop through the stocks to be bought
  for stock in stocks2buy:
    if(not exitFlag): #ensure that the exitFlag is not set
      #populate the information about the stock (either from the posList if it's present, else with default info)
      stockInfo = posList[algo][stock] if stock in posList[algo] else {
            "sharesHeld":0,
            "lastTradeDate":"NA",
            "lastTradeType":"NA",
            "buyPrice":0,
            "shouldSell":False,
            'sellAttempts':0,
            "note":""
          }
      
      #get the last date it was traded, if it isn't populated, just set it to yesterday
      try:
        lastTradeDate = dt.datetime.strptime(stockInfo[algo][stock]['lastTradeDate'],"%Y-%m-%d").date()
      except Exception:
        lastTradeDate = dt.date.today()-dt.timedelta(1)
      
      #to avoid day trading, make sure that it either didn't trade yet today, or if it has, that it hasn't sold yet
      if lastTradeDate < dt.date.today() and stockInfo['lastTradeType']!="sell":
        inf = n.getInfo(stock,['price','mktcap'])
        [curPrice, mktCap] = [inf['price'],inf['mktcap']]
        #set number of shares to be at most some % of the mktcap, otherwise as many int shares as cash is available (or 0 if curPrice is 0)
        if(curPrice>0): shares = int(min(cashPerStock/curPrice,(mktCap/curPrice)*float(c['account params']['maxVolPerc'])))
        else: shares = 0
        
        #print(mktCap,curPrice)
        #print(mktCap/curPrice,c['account params']['maxVolPerc'])
        #print(cashPerStock/curPrice,(mktCap/curPrice)*float(c['account params']['maxVolPerc']))

        if(verbose): print(f"{algo} - {stock} - {curPrice} - ok to buy {shares} shares")
        if(shares>0): #cannot place an order for 0 shares
          #market must be open in order to place the trade (this check is here in the event that the program is suspended while market open, then restarted while market closed)
          # if(n.marketIsOpen()): #TODO: add once this is confirmed, otherwise wait for a better solution to not need queries
          isBought = buy(shares,stock,algo,curPrice) #buy the stock
          if(isBought):
            print(f"buy\t{shares}\t{stock}\t{algo}\t{round(curPrice,2)}\t{round(shares*curPrice,2)}")
          else:
            print(f"could not buy {stock}")

          
    
#a stock has reached a trigger point and should begin to be checked more often (it will be sold in this function)
#this function is depreciated - replaced by checkTriggered
def triggeredUp(symb, algo):
  maxPrice = 0.01 #init vars to be slightly above 0
  curPrice = 0.01
  sellUpDn = float(eval(algo+".sellUpDn()"))
  #ensure that current price>0 (getPrice returns 0 if it can't recognize a symbol (eg if a merger happens or a stock is delisted)
  while(curPrice>0 and curPrice>=sellUpDn*maxPrice and n.timeTillClose()>60 and not exitFlag):
    curPrice = n.getInfo(symb)['price']
    maxPrice = max(maxPrice,curPrice)
    print(f"{algo}\t{symb}\t{round(curPrice/maxPrice,2)} : {round(sellUpDn,2)}")
    time.sleep(len(n.threading.enumerate())+2) #slow it down proportional to the number of threads running to not barage with requests
  isSold = sell(symb, algo)
  if(isSold): print(f"Sold all shares of {symb} for {algo} algo")

#run as long as the len of triggeredStocks>0 (where triggeredStocks is a set of format {"algo|symb"})
#TODO: this function really needs to be cleaned up (comments, better variables, more logical running)
#TODO: also add other checks for if a stock shouldn't be traded (like if price change is too high or sell attempts are too high)
def checkTriggered(verbose=False):
  #triggeredStocks = format of {"algo|symb"}
  global triggeredStocks
  lock = n.threading.Lock()
  maxPrices = {}
  #only run if there's stocks to sell and exit flag isn't triggered
  while(len(list(triggeredStocks))>0 and not exitFlag):
    if(verbose): print(f"{len(list(triggeredStocks))} stocks triggered for sale")

    #get prices for all stocks to sell
    prices = n.getPrices([e.split("|")[1]+"|stocks" for e in list(triggeredStocks)])

    #check for stocks in triggeredStocks that aren't in prices (some error occured that we hold it but it can't be traded)
    lock.acquire()
    for trigstock in list(triggeredStocks):
      if((trigstock.split("|")[1]+"|stocks").upper() not in prices):
        if(verbose): print(f"{trigstock} stored locally and in alpaca, but not in nasdaq. Removing from sellable stocks")
        triggeredStocks.discard(trigstock)

      sellAttempts = posList[trigstock.split("|")[0]][trigstock.split("|")[1]]['sellAttempts']
      if(sellAttempts>maxAttempts):
        if(verbose): print(f"{trigstock} attempted to sell too many times ({sellAttempts}/{maxAttempts}). Removing from sellable stocks")
        triggeredStocks.discard(trigstock)

    lock.release()
      
    print()
    

    #get the max prices of the stocks since watching
    maxPrices = {e:max(maxPrices[e],prices[e]['price']) if(e in maxPrices) else prices[e]['price'] for e in prices}

    for e in list(triggeredStocks):
      #get the sellUpDn %
      sellUpDn = eval(f"{e.split('|')[0]}.sellUpDn()")
      #get the current prices of the stocks
      curPrice = prices[(e.split("|")[1]+'|stocks').upper()]['price']
      #make sure that the price is valid
      if(curPrice>0):
        #sell once the current price drops below some % of the maxPrice since watching or within one minute of close
        if(curPrice>=sellUpDn*maxPrices[(e.split('|')[1]+"|stocks").upper()] and n.timeTillClose()>60):
          print(f"{e.split('|')[0]}\t{e.split('|')[1]}\t{round(curPrice/maxPrices[(e.split('|')[1]+'|stocks').upper()],3)} : {sellUpDn}")
        else:
          sell(e.split("|")[1],e.split("|")[0])          
          #this shouldn't be necessary since it's supposed to be handled in sell(), but it seems to have issues there and not existing the thread
          # triggeredStocks.discard(e)
      else:
        print(f"{e} current price is $0. Selling")
        sell(e.split("|")[1],e.split("|")[0])
        # triggeredStocks.discard(e)

    print()
    time.sleep(max(5,len(list(triggeredStocks))/5)) #wait at least 5 seconds between checks, and if there are more, wait longer
    
#multiplex check2sell where pos is the output of a.getPos()
#determine if the stocks in the algo are good sells (return dict of {symb:goodSell(t/f)})
def check2sells(pos,verbose=False):
  global triggeredStocks
  
  print("algo\tshares\tsymb \tcng frm buy\tcng frm cls\ttriggers\tnotes")
  print("----\t------\t-----\t-----------\t-----------\t-----------\t----------")
  
  for algo in posList:
    if(verbose): print(algo)
    #only the stocks in both posList[algo] and held positions
    #the stocks held by the given algo
    symbList = [e for e in pos if e['symbol'] in posList[algo]]
    
    #TODO: in each algo, add an error report if there's a stock that doesn't appear to be tradable (that is, it's in symbList but doesn't show up in getPrices)
    
    #get whether the stocks are good sells or not
    gs = eval(f"{algo}.goodSells(symbList,verbose=False)")
    
    
    
    #go through the stocks of the algo
    for e in symbList:
      #only display/sell if not bought today and it hasn't tried to sell more than the max times already
      if((posList[algo][e['symbol']]['lastTradeDate']<str(dt.date.today()) or 
      posList[algo][e['symbol']]['lastTradeType']!='buy') and
      posList[algo][e['symbol']]['sellAttempts']<maxAttempts):
        
        print(f"{algo}\t",
              f"{int(posList[algo][e['symbol']]['sharesHeld'])}\t",
              f"{e['symbol']}\t",
              f"{bcolor.FAIL if round(float(e['unrealized_plpc'])+1,2)<1 else bcolor.OKGREEN}{round(float(e['unrealized_plpc'])+1,2)}{bcolor.ENDC}\t\t",
              f"{bcolor.FAIL if round(float(e['unrealized_intraday_plpc'])+1,2)<1 else bcolor.OKGREEN}{round(float(e['unrealized_intraday_plpc'])+1,2)}{bcolor.ENDC}\t\t",
              str(round(eval(f'{algo}.sellDn("{e["symbol"]}")'),2))+" & "+
              str(round(eval(f'{algo}.sellUp("{e["symbol"]}")'),2))+"\t",
              f"{posList[algo][e['symbol']]['note']}",sep="")
        
        
        #ensure that the market is open in order to actually place a trade
        #this check is here in the event that the program is suspended while open, then restarted while closed
        # if(n.marketIsOpen()): #TODO: confirm that this is needed first and not a setting that can be changed outside of this script
        if(gs[e['symbol']]==-1): #if it sells down (stop-loss)
          #sell immediately
          sell(e['symbol'],algo)
        elif(gs[e['symbol']]==1): #else if the stock is a good sell (sellUp)
          if(algo+"|"+e['symbol'] not in triggeredStocks): #make sure that it's not already present
            triggeredStocks.add(algo+"|"+e['symbol']) #if not, then add it to the triggered list
          if("triggered" not in [t.name for t in n.threading.enumerate()]): #make sure that the triggered list isn't already running
            triggerThread = n.threading.Thread(target=checkTriggered) #init the thread - note locking is required here
            triggerThread.name = "triggered" #set the name to the algo and stock symb
            triggerThread.start() #start the thread
  
  
#basically just a market order for the stock and then record it into an order info file
#return True if it sells, False if it doesn't
def sell(stock, algo, verbose=False):
  global posList, cashList,triggeredStocks

  #determine the current price and the number of shares to sell (they should already be floats, but recasting just in case)
  sellPrice = float(n.getInfo(stock)['price'])
  sharesHeld = float(posList[algo][stock]["sharesHeld"])
  sellAttempts = int(posList[algo][stock]['sellAttempts'])

  #ensure there are sellable shares
  if(sharesHeld>0 and sellAttempts<maxAttempts):
    if(verbose): print(f"Attempting to sell {sharesHeld} shares of {stock} at ${round(sellPrice,2)}/share")
    #sell them
    r = a.createOrder(side="sell",qty=sharesHeld,symb=stock,verbose=False)
  else:
    print(f"No shares held of {stock} or too many sell attempts made ({sellAttempts}/{maxAttempts})")
    triggeredStocks.discard(algo+"|"+stock)
    return False
  
  #see how it looks in here: https://alpaca.markets/docs/trading-on-alpaca/orders/#order-lifecycle
  #TODO: not sure what else to check for in status?
  #check that it actually sold
  if(sellAttempts<maxAttempts and 'status' in r and r['status'] in ["accepted",'pending_new','filled','done_for_day','new']):
    if(verbose): print(f"status is {r['status']}")
    cashList[algo]['earned'] += sellPrice*sharesHeld #update the cash earned by the sale
    posList[algo][stock] = { #update the entry in posList
        "sharesHeld":0,
        "lastTradeDate":str(dt.date.today()),
        "lastTradeType":"sell",
        "buyPrice":0,
        "shouldSell":False,
        'sellAttempts':0,
        "note":""
      }
    triggeredStocks.discard(algo+"|"+stock)

    print(f"Sold {algo}'s shares of {stock}")
    isSold = True

  #check specifically for if the stock cannot be sold due to a 403 error
  elif('code' in r and str(r['code']).startswith("403")):
    if(sellAttempts<maxAttempts):
      posList[algo][stock]['sellAttempts'] += 1
      print(f"failed to sell {sharesHeld} shares of {stock}. (attempt {sellAttempts+1} of {maxAttempts})")
      isSold = False
    else:
      print(f"max attempts exceeded trying to sell {stock} - {sellAttempts+1}/{maxAttempts}. Removing from sellable stocks")
      posList[algo][stock]['shouldSell'] = False
      posList[algo][stock]['lastTradeType'] = 'sell'
      posList[algo][stock]['lastTradeDate'] = str(dt.date.today())
      triggeredStocks.discard(algo+"|"+stock)
      isSold = False

  #check for any other reason
  else:
    posList[algo][stock]['sellAttempts'] += 1
    print(f"Order to sell {sharesHeld} shares of {stock} for {algo} not accepted (attempt {sellAttempts+1} of {maxAttempts})")
    print(r)
    isSold = False


  #update the poslist file
  lock = n.threading.Lock()
  lock.acquire()
  with open(c['file locations']['posList'],'w') as f:
    f.write(json.dumps({'algos':posList,'cash':cashList},indent=2))
    f.close()
  lock.release()

  return isSold



#basically just a market buy of this many shares of this stock for this algo
#return True if it buys successfully, false if not
def buy(shares, stock, algo, buyPrice):
  r = a.createOrder(side="buy",qty=shares,symb=stock) #this needs to happen first so that it can be as accurate as possible
  global posList, cashList

  if('status' in r and r['status'] == "accepted"): #check to make sure that it actually bought - TODO: does the presence of 'status' indicate that it bought or not?
    lock = n.threading.Lock()
    lock.acquire()
    posList[algo][stock] = { #update the entry in posList
        "sharesHeld":float(posList[algo][stock]['sharesHeld'])+float(r['qty']) if stock in posList[algo] else float(r['qty']),
        "lastTradeDate":str(dt.date.today()),
        "lastTradeType":"buy",
        #running avg = (prevAvg*n+newAvg*m)/(n+m)
        "buyPrice":(posList[algo][stock]['buyPrice']*posList[algo][stock]['sharesHeld']+buyPrice*float(r['qty']))/(posList[algo][stock]['sharesHeld']+float(r['qty'])) if stock in posList[algo] else buyPrice,
        "shouldSell":False,
        "sellAttempts":0,
        "note":algoList[algo][stock] if stock in algoList[algo] else ""
      }
      
    cashList[algo]['invested'] += buyPrice*shares
    open(c['file locations']['posList'],'w').write(json.dumps({'algos':posList,'cash':cashList},indent=2)) #update posList file
    lock.release()
    return True
  else: #it didn't actually buy
    print(f"Order to buy {shares} shares of {stock} not accepted")
    return False


#set up the position list and do some error checking to make sure it's correct (take list of algos as arg in the event the pos list needs to be populated)
def setPosList(algoList, verbose=True):
  posList={}
  cashList = {}
  #if the posList file doesn't exist
  if(not os.path.isfile(c['file locations']['posList'])):
    if(verbose): print("posList file is missing. Creating and adding blank lists...")
    lock = n.threading.Lock()
    lock.acquire()
    with open(c['file locations']['posList'],'w') as f:
      f.write(json.dumps({'algos':{e:{} for e in algoList},'cash':{e:{"earned":0,"invested":0} for e in algoList}})) #write a empty algos and 0 cash for all algos to the posList file
    #lists is the data directly from the posList file
    lists = json.loads(open(c['file locations']['posList'],'r').read())
    #posList contains only the positions
    posList = lists['algos']
    #cashList contains only the cash
    cashList = lists['cash']
    lock.release()
  else: #if it does exist
    # try: #try reading any json data from it
    lock = n.threading.Lock()
    lock.acquire()
    with open(c['file locations']['posList'],'r') as f:
      lists = json.loads(f.read())
    
    posList = lists['algos']
    cashList = lists['cash']
      
    #algos that are being used but not in the posList
    missingAlgos = [algo for algo in algoList if algo not in posList]
    for algo in missingAlgos:
      if(verbose): print(f"Adding {algo} to posList")
      posList[algo] = {}

    missingCash = [algo for algo in algoList if algo not in cashList]
    for algo in missingCash:
      if(verbose): print(f"Adding {algo} to cashList")
      cashList[algo] = {'earned':0,'invested':0}
    
    lock.release()

    #write the missing algos to the file
    lock = n.threading.Lock()
    lock.acquire()
    with open(c['file locations']['posList'],'w') as f:
      f.write(json.dumps({'algos':posList,'cash':cashList}))
    lock.release()
    '''
    except Exception: #if it fails, then just write the empty algoList to the file
      #TODO: this is dangerous! This could potentially overwrite all saved position data if there's any error above. TODO Make this more robust
      if(verbose): print("Something went wrong. Overwriting poslist file")
      lock = n.threading.Lock()
      lock.acquire()
      with open(c['file locations']['posList'],'w') as f:
        f.write(json.dumps({'algos':{e:{} for e in algoList},'cash':{e:{"earned":0,"invested":0} for e in algoList}})) #write a empty algos and 0 cash for all algos to the posList file
      lists = json.loads(open(c['file locations']['posList'],'r').read())
      posList = lists['algos']
      cashList = lists['cash']
      lock.release()
    '''
  return [posList,cashList]


#sync what we have recorded and what's actually going on in the account
#TODO: if not done already, need to make sure that when the posList says there's 0 shares held, but getPos says there's shares, that the share amounts are transferred
def syncPosList(verbose=False):
  global posList, cashList
  lock = n.threading.Lock() #locking is needed to write to the file and edit the posList var (will have to see how threads and globals work with each other)
  print(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"Syncing posList...")
  
  if(verbose): print("getting actually held positions")
  p = a.getPos()
  heldPos = {e['symbol']:float(e['qty']) for e in p} #actually held positions
  heldBuyPrices = {e['symbol']:float(e['avg_entry_price']) for e in p} #get the actual buy prices for each stock

  if(verbose): print("Adding any missing fields to current records")
  for algo in posList:
    for symb in posList[algo]:
      lock.acquire()      
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
      if('sellAttempts' not in posList[algo][symb]):
        if(verbose): print(f"{algo} {symb} missing sellAttempts")
        posList[algo][symb]['sellAttempts'] = 0
      if('note' not in posList[algo][symb]):
        if(verbose): print(f"{algo} {symb} missing note")
        posList[algo][symb]['note'] = algoList[algo][symb] if(algo in algoList and symb in algoList[algo]) else ""
      lock.release()


  #check if an algo in the posList is removed from the algoList
  for inactiveAlgo in [algo for algo in posList if algo not in algoList]:
    if(verbose): print(f"Looking at inactive algo {inactiveAlgo}")
    #stocks that are in a removed algo should be moved to an active algo that has it, if none do, then move it to the active algo with the highest loss
    if(inactiveAlgo in cashList):
      if(verbose): print(f"Removing {inactiveAlgo} from cashList")
      cashList.pop(inactiveAlgo,None)
    
    #move the stocks from the inactive algo to active ones
    for symb in posList[inactiveAlgo]: #stocks in the removed algo
      #get all active algos that contain it
      activeAlgosWithStock = [e for e in posList if(e in algoList and symb in e)]
      maxAlgo = ['x',0] #algo and the max gain of the stock
      #get the algo with the max gain for this stock
      if(len(activeAlgosWithStock)>0): #if there's at least 1 active algo that contains it
        for activeAlgo in activeAlgosWithStock: #look thru each algo that could hold the stock
          sellUp = eval(f"{activeAlgo}.sellUp('{symb}')") #find the sell up of that algo
          maxAlgo = [activeAlgo,sellUp] if sellUp>maxAlgo[1] else maxAlgo #get the greater of the two algos
      else: #if there are not active algos that contain it
        for activeAlgo in algoList: #then loop through all active algos
          sellUp = eval(f"{activeAlgo}.sellUp('{symb}')") #find the sell up of that algo
          maxAlgo = [activeAlgo,sellUp] if sellUp>maxAlgo[1] else maxAlgo #get the greater of the two algos

      if(verbose): print(f"{inactiveAlgo} algo is inactive. Moving {symb} from {inactiveAlgo} to {maxAlgo[0]}")
      
      lock.acquire()
      try: #this should evaluate if the symb is already present in the active algo
        posList[maxAlgo[0]][symb]['sharesHeld'] += posList[inactiveAlgo][symb]['sharesHeld'] #only transfer over the shares active algo data is more important
      except Exception: #this should evaluate if the symb is not already present in the active algo
        posList[maxAlgo[0]][symb] = { #transfer over all data from the inactive one
                                  'sharesHeld':posList[inactiveAlgo][symb]['sharesHeld'],
                                  'lastTradeDate':posList[inactiveAlgo][symb]['lastTradeDate'],
                                  'lastTradeType':posList[inactiveAlgo][symb]['lastTradeType'],
                                  'buyPrice':posList[inactiveAlgo][symb]['buyPrice'],
                                  'shouldSell':posList[inactiveAlgo][symb]['shouldSell'],
                                  'sellAttempts':posList[inactiveAlgo][symb]['sellAttempts'],
                                  'note':posList[inactiveAlgo][symb]['note']
                                }
        
      posList[inactiveAlgo][symb]['sharesHeld'] = 0 #remove the shares fromt he inactive algo
      lock.release()
        
    del posList[inactiveAlgo] #remove the inactive algo from the 
  
  
  
  #total stocks in posList
  if(verbose): print("getting recorded positions...")
  recPos = {} #recorded positions
  for algo in posList: #for every algo in the posList
    if(len(posList)>0):
      for stock in posList[algo]: #for every stock in that algo
        if stock not in recPos: #if that stock isn't already in the recorded positions
          recPos[stock] = float(posList[algo][stock]['sharesHeld']) #add it
        else:
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
        lock.acquire()
        posList[algo].pop(symb,None) #remove from posList
        lock.release()
      recPos.pop(symb,None) #remove from recorded
    
    #for each stock, if there are an excess of shares in the recPos than the heldPos, look for any in the algos that match the disparity, and remove them from that algo
      #if none match (i.e. heldPos and recPos both have a stock, but there's an unknown amount extra in recPos), then trim off the amount extra from the algo that has the most above the disparity
        #if no algo has any above it: then sell the whole lot TODO: this should probably be handled differently, but it's some complexity that can be saved for later
    for symb in [s for s in recPos if recPos[s]>heldPos[s]]: #for all stocks where the recorded is greater than the held
      for algo in posList: #for every algo
        #remove any that may be exact matches
        if(symb in posList[algo] and float(posList[algo][symb]['sharesHeld'])==recPos[symb]-heldPos[symb]):
          if(verbose): print(f"Removing {float(posList[algo][symb]['sharesHeld'])} shares of {symb} from {algo} records")
          recPos[symb] -= float(posList[algo][symb]['sharesHeld'])
          if(recPos[symb]==0):
            recPos.pop(symb,None)
          lock.acquire()
          posList[algo].pop(symb,None)
          lock.release()
          
          
      #if there's still a discrepency (ie. there is not an exact difference)
      if(recPos[symb]>heldPos[symb]): #if the recorded still has more than the held
        #get algos with the symbol and the number of shares of that symbol
        if(verbose): print(f"more shares of {symb} in records than actuals")
        algosWithStock = {e:float(posList[e][symb]['sharesHeld']) for e in posList if symb in posList[e]} #get the number of shares per algo if the algo has the stock
        for algo in algosWithStock:
          #TODO: this should probably be changed to spread out over multiple algos rather than just 1
          if(algosWithStock[algo]>=recPos[symb]-heldPos[symb]): #if an algo has more than the disparity
            if(verbose): print(f"{algo} has {algosWithStock[algo]} shares of {symb}. Removing {recPos[symb]-heldPos[symb]} shares")
            lock.acquire()
            posList[algo][symb]['sharesHeld'] -= recPos[symb]-heldPos[symb] #remove the disparity
            lock.release()
            recPos[symb] -= recPos[symb]-heldPos[symb]
            break

        if(recPos[symb]>heldPos[symb]): #if the disparity wasn't caught, then just sell the lot
          print(f"Could not find a suitable sync for {symb}. Selling the lot.")
          for algo in [algo for algo in posList if symb in posList[algo]]:
            sell(symb, algo)



    #compare heldPos to recPos

    #ensure algoList is up to date
  if(not eq(recPos, heldPos) or not os.path.isfile(c['file locations']['buyList'])): #compare again after the initial comparison
    if(verbose): print(f"Discrepency still present or buyList file is missing. Updating buy list")
    #if the lists aren't currently updating and haven't already updated today, then update
    if(not listsUpdatedToday and len([t for t in n.threading.enumerate() if t.name.startswith('update')])==0):
      updateListsThread = n.threading.Thread(target=updateLists) #init the thread - note locking is required here
      updateListsThread.name = 'updateLists' #set the name to the stock symb
      updateListsThread.start() #start the thread

    if(verbose): print("Waiting for stock lists to finish updating...")
    while(not listsUpdatedToday or len([t for t in n.threading.enumerate() if t.name.startswith('update')])>0): #wait for the lists to finish updating
      # print([t.name for t in n.threading.enumerate() if t.name.startswith('update')])
      time.sleep(2)
    if(verbose): print("lists done updating for syncPosList")

    #check that symb is somewhere in algoList
    #if it is, then add it to the algo that has it with the highest gain
    #else append it to the algo with the smallest gain
    for symb in [s for s in heldPos if s not in recPos]: #for all stocks actually held and not recorded

      algosWithStock = [e for e in algoList if symb in algoList[e]] #try and find a home for a stock by looking in the stocks to be bought (get all algos that may have it)
      if(len(algosWithStock)>0): #if an algo has it
        maxAlgo = ['x',0] #algo and the max gain of the stock
        #get the algo with the max gain for this stock
        for algo in algosWithStock: #look thru each algo that could hold the stock, and give it to the one with the most gain potential
          sellUp = eval(f"{algo}.sellUp('{symb}')") #find the sell up of that algo
          maxAlgo = [algo,sellUp] if sellUp>maxAlgo[1] else maxAlgo #get the greater of the two algos
        if(verbose): print(f"Adding {heldPos[symb]} shares of {symb} to {maxAlgo[0]}.")
        lock.acquire()
        posList[maxAlgo[0]][symb] = {'lastTradeDate':'NA',
                                     'lastTradeType':'NA',
                                     'sharesHeld':heldPos[symb],
                                     'buyPrice':heldBuyPrices[symb],
                                     'shouldSell':False,
                                     'sellAttempts':0,
                                     'note':algoList[maxAlgo[0]][symb]
                                    }
        lock.release()
        recPos[symb]=heldPos[symb] #also add the stock to the recPos temp var
        
      else: #if no algo has it, give it to the algo with the least amount of loss
        minAlgo = ['x',100] #algo and the acceptable loss of the stock
        for algo in algoList: #for every algo that'll potentially gain
          sellUp = eval(f"{algo}.sellUp('{symb}')") #get the sell dn of each algo
          minAlgo = [algo,sellUp] if sellUp<minAlgo[1] else minAlgo #get the greater of the the two algos
        #add to the algo with the least gain (to get rid of asap)
        if(verbose): print(f"No algo found to have {symb}. Adding {heldPos[symb]} shares to {minAlgo[0]}.")
        lock.acquire()
        posList[minAlgo[0]][symb] = {'lastTradeDate':'NA',
                                     'lastTradeType':'NA',
                                     'sharesHeld':heldPos[symb],
                                     'buyPrice':heldBuyPrices[symb],
                                     'shouldSell':False,
                                     'sellAttempts':0,
                                     'note':algoList[minAlgo[0]][symb] if symb in algoList[minAlgo[0]] else ""
                                    }
        lock.release()
        recPos[symb]=heldPos[symb] #also add the stock to the recPos temp var

    #find symbols that have more actual shares than recorded shares
    #add the shares to the algo with the highest gain
    for symb in [s for s in heldPos if heldPos[s]>recPos[s]]: #for all stocks where the actual is greater than the recorded
      algosWithStock = [e for e in posList if symb in posList[e] and e in algoList] #get all currently used algos holding the stock
      
      maxAlgo = algosWithStock[0] #init maxAlgo to the first algo in the list
      for algo in algosWithStock[1:]: #get the algo with the max gain potential and ensure that the symb is in the algo (skip the first one since it's the init value - save a loop)
        maxAlgo = algo if eval(f"{algo}.sellUp(symb)")>eval(f"{maxAlgo}.sellUp('{symb}')") else maxAlgo #get the algo with the largest sellUp value
      
      lock.acquire()
      posList[maxAlgo][symb]['sharesHeld'] += heldPos[symb]-recPos[symb] #add in the disparity
      lock.release()
      
  #remove any symbs that have 0 shares, remove any algos that have 0 symbs
  if(verbose): print("Removing blanks")
  for algo in list(posList):
    for symb in list(posList[algo]): #must be cast as list in order to not change dict size (this makes a copy)
      if(posList[algo][symb]['sharesHeld']==0):
        lock.acquire()
        posList[algo].pop(symb,None)
        lock.release()
    if(algo not in algoList and len(posList[algo])==0): #remove any algos that aren't in the algoList and have 0 symbs in them
      lock.acquire()
      posList.pop(algo,None)
      lock.release()
  
  for algo in posList:
    if(verbose): print(f"Calculating invested amount in {algo}... ")
    algoamt = 0
    for s in posList[algo]:
      #calcuate amount per stock
      stockamt = posList[algo][s]['sharesHeld']*posList[algo][s]['buyPrice']
      if(verbose): print("  ",s,round(stockamt,2))
      #add to the algo total
      algoamt += stockamt
    #store the algo total in the amount invested
    cashList[algo]['invested'] = algoamt

    if(verbose): print(algo,round(cashList[algo]['invested'],2),"\n")
  
  if(verbose): print("Marking to be sold")
  revSplits = n.reverseSplitters()
  for algo in posList:
    for symb in posList[algo]:
      if(posList[algo][symb]['sellAttempts']<maxAttempts and symb in revSplits):
        if(verbose): print(f"{algo} - {symb} marked for sale")
        lock.acquire()
        posList[algo][symb]['shouldSell'] = True
        lock.release()
  
  #write to the file
  lock.acquire()
  with open(c['file locations']['posList'],'w') as f:
    if(verbose): print("Writing to posList file")
    f.write(json.dumps({'algos':posList,'cash':cashList},indent=2))
  lock.release()
  print(dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),"Done syncing posList")




#run the main function
if __name__ == '__main__':
  global exitFlag
  exitFlag = False #set to true if the program stopped by ctrl+c

  try:
    main(verbose=False) #start running the program
  except KeyboardInterrupt: #exit on ctrl+c
    print("Exiting")
    exitFlag=True
    
  except Exception: #record unhandled exceptions
    print("An unhandled error was encountered. Please check the log.")
    #current time
    now = dt.datetime.now()
    #get the traceback message
    tbmsg = traceback.format_exc()
    #display it
    print(tbmsg)
    #append to error file
    with open(c['file locations']['errLog'],'a+') as f:
      f.write("\n"+str(now)+tbmsg+"\n")
      f.close()
