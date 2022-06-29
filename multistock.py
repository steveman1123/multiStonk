import _multistonks.otherfxns as o
import _multistonks.alpacafxns as a
import random, time, json, sys, os, traceback
from glob import glob
from operator import eq
import datetime as dt
from colorama import init as colorinit
HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


print(WARNING+"\nStarting up..."+ENDC)

colorinit() #allow coloring in Windows terminals


# parse args and get the config file
configFile = "./configs/multi.config"

# set the multi config file
c = o.configparser.ConfigParser()
c.read(configFile)

# list of algorithms to be used and their corresponding stock lists to be bought (init with none)
# var comes in as a string, remove spaces, and turn into comma separated list
algoList = c['allAlgos']['algoList'].replace(" ", "").split(',')
algoList = {e: {} for e in algoList}

# tell the user general setting information
print(f"Config file\t{configFile}")
print(f"Key file \t{c['file locations']['keyFile']}")
print(f"posList file\t{c['file locations']['posList']}")
print(f"buyList file\t{c['file locations']['buyList']}")
print(f"Error log \t{c['file locations']['errLog']}")
print("Using the algos: ", end="")
print(*list(algoList), sep=", ", end="\n\n")


a.init(c['file locations']['keyFile'], int(c['account params']['isPaper']))

# add the algos dir
sys.path.append(c['file locations']['stockAlgosDir'])

# import all algos that are in algoList (they require an up-to-date posList, so must be imported after it's updated)
for algo in algoList:
    exec(f"import {algo}")


# tell everyone whether the list has been updated yet today or not
listsUpdatedToday = False
# get the time in datetime format of when the market closes (reference this when looking at time till close)
closeTime = o.closeTime(estOffset=-1)

# extra cash to hold above hold value
minCashMargin = float(c['account params']['minCashMargin'])
if(minCashMargin < 1):  # minCashMargin MUST BE GREATER THAN 1 in order for it to work correctly
    raise ValueError(
        "Error: cash margin is less than 1. Multiplier must be >=1")
minCash2hold = float(c['account params']['minCash2hold'])
maxCash2hold = float(c['account params']['maxCash2hold'])



# main function to run continuously
def main(verbose=False):
    # values to be used across functions and are edited here
    global algoList, posList, listsUpdatedToday, closeTime, cashList, triggeredStocks

    triggeredStocks = set()  # should contain elements of format algo|stock
    ask2sell = True  # if this is true, then the program will ask to sell all if portval drops below some % of maxPortVal
    # check that the keys being used are valid
    a.checkValidKeys(int(c['account params']['isPaper']))
    if(len(a.getPos()) == 0):
        print(
            f"Will start buying {c['time params']['buyTime']} minutes before next close")

    # initiate/populate the list of positions by algo
    [posList, cashList] = setPosList(algoList)
    # init the algos
    for algo in algoList:
        exec(f"{algo}.init('{configFile}')")

    syncPosList()  # in the event that something changed during the last run, this should catch it
    print("\n")  # leave a space between startup and main sequence

    if(verbose):
        print(json.dumps(algoList, indent=2))

    # get the closing prices of the portfolio over the last month
    #TODO: call Robinhood api here. 
    portHist = a.getProfileHistory(str(dt.date.today()), '1M')['equity']
    # get the max portfolio value over the last month and remove blank entries
    maxPortVal = max([e for e in portHist if e is not None])
    isManualSellOff = not int(c['account params']['portAutoSellOff'])
    while True:
        acct = a.getAcct()  # get account info
        pos = a.getPos()  # get all held positions (no algo assigned)

     
        if(ask2sell and float(acct['portfolio_value']) < maxPortVal*float(c['account params']['portStopLoss']) and len(pos) > 0):
                print(
                    f"Portfolio value of ${acct['portfolio_value']} is less than {c['account params']['portStopLoss']} times the max portfolio value of ${maxPortVal}.")
                if(not isManualSellOff):
                    print("Automatically selling all...")
                # if the portfolio value falls below our stop loss, automatically sell everything
                soldAll = a.sellAll(isManual=isManualSellOff)
                if(soldAll):
                    break  # stop the program if the selling occured
                if(isManualSellOff):  # if the selling is set to manual, then ask if the user wants to keep being asked to sell all or not
                    ask2sell = (
                        input("Ask to sell all again today (y/n)? ").lower()) != "n"
                    if(ask2sell):
                        print("Will continue asking to sell all today")
                    else:
                        print("Will ask to sell all again tomorrow")

        totalCash = float(acct['cash']) #TODO: get this from Robinhood API
        tradableCash = getTradableCash(totalCash, maxPortVal)

        if(o.marketIsOpen()):
            print(f"\nPortfolio Value: ${acct['portfolio_value']}, total cash: ${round(totalCash,2)}, tradable cash: ${round(tradableCash,2)}, port stop loss: {maxPortVal*float(c['account params']['portStopLoss'])},  {len(posList)} algos | {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            # update the lists if not updated yet and that it's not currently updating
            if(not listsUpdatedToday and len([t.getName() for t in o.threading.enumerate() if t.getName().startswith('update')]) == 0):
                    # init the thread - note locking is required here
                    updateListsThread = o.threading.Thread(target=updateLists)
                    # set the name to the stock symb
                    updateListsThread.setName('updateLists')
                    updateListsThread.start()  # start the thread

            print("algo\tshares\tsymb \tcng frm buy\tcng frm cls\ttriggers\tnotes")
            print("----\t------\t-----\t-----------\t-----------\t-----------\t----------")
            check2sells(pos)

            if((closeTime-dt.datetime.now()).total_seconds() <= 60*float(c['time params']['buyTime']) and sum([t.getName().startswith('update') for t in o.threading.enumerate()]) == 0):
                    # account for withholding a certain amount of cash+margin
                    tradableCash = getTradableCash(totalCash, maxPortVal)
                    # evenly split available cash across all algos
                    cashPerAlgo = tradableCash/len(algoList)
                    # start buying things
                    # print(tradableCash,cashPerAlgo,algoList,sep="\n")
                    for algo in algoList:
                        if(verbose):
                            print(f"starting buy thread {algo}")
                        buyThread = o.threading.Thread(target=check2buy, args=(
                            algo, cashPerAlgo, list(algoList[algo]), False))  # init the thread
                        buyThread.setName(algo)  # set the name to the algo
                        buyThread.start()  # start the thread

            time.sleep(60)
        else:
            print("Algo ROI estimates:")
            for algo in posList:
                # get the current prices of all the stocks in a given algo
                curPrices = o.getPrices([e+"|stocks" for e in posList[algo]])
                algoCurVal = sum([posList[algo][s]['sharesHeld']*curPrices[s+"|stocks".upper()]['price'] for s in posList[algo] if s+"|stocks".upper()
                                in curPrices])+cashList[algo]['earned']  # get the total value of the stocks in a given algo plus the returned cash
                if(cashList[algo]['invested'] == 0):
                    cashList[algo]['invested'] = sum(
                        [posList[algo][s]['sharesHeld']*posList[algo][s]['buyPrice'] for s in posList[algo]])
                # set the investment amount (technically could be removed, but easier to just keep it)
                algoBuyVal = cashList[algo]['invested']

                if(algoBuyVal > 0):
                    roi = round(algoCurVal/algoBuyVal, 2)
                else:
                    roi = 1
                print(f"{algo} - {FAIL if roi<1 else OKGREEN}{roi}{ENDC}")
            portHist = a.getProfileHistory(str(dt.date.today()), '1M')
            portHist = {str(dt.datetime.fromtimestamp(portHist['timestamp'][i]).date(
            )): portHist['equity'][i] for i in range(len(portHist['timestamp'])) if portHist['equity'][i] is not None}
            # get the max portfolio value of the last month
            maxPortVal = max(list(portHist.values()))

            # display max val and date
            print(
                f"\nHighest portVal in the last month: ${round(maxPortVal,2)} on {list(portHist.keys())[list(portHist.values()).index(maxPortVal)]}")
            print(
                f"Current portVal: ${round(portHist[max(list(portHist.keys()))],2)} ({round(100*portHist[max(list(portHist.keys()))]/maxPortVal,3)}% of highest)")
            print(
                f"Port stop-loss: ${round(float(c['account params']['portStopLoss'])*maxPortVal,2)} ({round(100*float(c['account params']['portStopLoss']),2)}% of highest)\n")
            syncPosList()  # sync up posList to live data
            if(o.dt.date.today().weekday() == 4 and o.dt.datetime.now().time() > o.dt.time(12)):
                print("Removing saved csv files")
                for f in glob(o.c['file locations']['stockDataDir']+"*.csv"):
                    try:  # placed inside a try statement in the event that the file is removed before being removed here
                            o.os.unlink(f)
                    except Exception:
                        pass


            print("Clearing buyList")
            algoList = {e: {} for e in algoList}

            # reset ask2sell in order to ask again tomorrow
            ask2sell = True
            tto = a.timeTillOpen()
            print(f"Market opens in {round(tto/3600,2)} hours")
            # wait some time before the market opens
            if(tto > 60*float(c['time params']['updateLists'])):
                print(
                    f"Updating stock lists in {round((tto-60*float(c['time params']['updateLists']))/3600,2)} hours\n")
                time.sleep(tto-60*float(c['time params']['updateLists']))
            # TODO: move this into the thread or within the thread have a "done updating buylist"
            print("Updating buyList")
            # init the thread - note locking is required here
            updateListsThread = o.threading.Thread(target=updateLists)
            updateListsThread.setName('updateLists')  # set the name to the stock symb
            updateListsThread.start()  # start the thread

            closeTime = o.closeTime(estOffset=-1)  # get the next closing time
            time.sleep(a.timeTillOpen())


# given the total cash and cash parameters, return the tradable cash
def getTradableCash(totalCash, maxPortVal, verbose=False):
    if(totalCash < minCash2hold):  # 0-999
        if(verbose):
            print(1)
        return totalCash
    elif(minCash2hold <= totalCash <= minCash2hold*minCashMargin):  # 1000-1100
        if(verbose):
            print(2)
        return 0
    elif(minCash2hold*minCashMargin < totalCash < maxPortVal*maxCash2hold):  # 1101-.25*max
        if(verbose):
            print(3)
        return totalCash-minCash2hold*minCashMargin
    else:  # .25*max-inf
        if(verbose):
            print(4)
        if(verbose):
            print(maxPortVal*maxCash2hold, minCash2hold*minCashMargin)
        return totalCash-max(maxPortVal*maxCash2hold, minCash2hold*minCashMargin)




def updateLists(verbose=False):
    global algoList, listsUpdatedToday
    # check that the buyfile is present and if it was updated today: if it was, then read directly from it, else generate lists
    errored = False
    if(verbose):
        
        print("Checking if buyList file is present")
    if(o.os.path.isfile(c['file locations']['buyList'])):
        if(verbose):
            print("File is present. Checking mod date")
        try:
            # if ANYONE knows of a better way to get the modified date into a date format, for the love of god please let me know
            modDate = dt.datetime.strptime(time.strftime("%Y-%m-%d", time.localtime(
                os.stat(c['file locations']['buyList']).st_mtime)), "%Y-%m-%d").date()
        except Exception:
            modDate = dt.date.today()-dt.timedelta(1)
        if(modDate == dt.date.today()):
            try:
                if(verbose):
                    print("Reading from file")
                f = json.loads(
                    open(c['file locations']['buyList'], 'r').read())
                if(len([e for e in f if e not in algoList]) > 0 or len([e for e in algoList if e not in f]) > 0):
                    if(verbose):
                        print("mismatch between saved buy list and algos being used")
                    errored = True
                else:
                    algoList = f  # valid file, valid data, so should just read from the file
            except Exception:
                if(verbose):
                    print("invalid data in file")
                errored = True
        else:
            if(verbose):
                print(f"mod date not today - {modDate}")
            errored = True
    else:
        if(verbose):
            print("file does not exist")
        errored = True
    # TODO: check that all algos in the algolist are present in the buy list as well (in the event that an algo has been added or removed after updating today
    if(errored):

        lock = o.threading.Lock()
        revSplits = o.reverseSplitters()
        for e in algoList:  # start a thread to update the list for each algorithm
            # print(f"updating {e} list")
            # init the thread - note locking is required here
            updateThread = o.threading.Thread(
                target=updateList, args=(e, lock, revSplits))
            updateThread.setName("update-"+e)  # set the name to the stock symb
            updateThread.start()  # start the thread

        # TODO: see the following because the updateList threads currently all access algoList, and the while loop is probably not the best solution for waiting
        # https://www.geeksforgeeks.org/multio.threading-in-python-set-2-synchronization/
        # wait for the threads to finish updating, or the exitFlag is triggered
        while(len([t.getName() for t in o.threading.enumerate() if t.getName().startswith("update-")]) > 0 and not exitFlag):
            time.sleep(2)

        if(not exitFlag):
            # save to a file
            if(verbose):
                print("Writing to buyList file")
            with open(c['file locations']['buyList'], 'w') as f:
                f.write(json.dumps(algoList, indent=2))

    listsUpdatedToday = True

def updateList(algo, lock, rm=[], verbose=True):
    global algoList
    if(not exitFlag):  # ensure that the exit flag isn't set
        if(verbose):
            print(f"Updating {algo} list")
        # TODO: exitFlag doesn't stop individual getList()'s. Might not be a bad idea to read it somehow?
        # this is probably not safe, but best way I can think of
        algoBuys = eval(algo+".getList()")
        # remove any stocks that are in the rm list
        algoBuys = {e: algoBuys[e] for e in algoBuys if e not in rm}
        lock.acquire()  # lock in order to write to the list
        algoList[algo] = algoBuys
        lock.release()  # then unlock


'''
#check to sell positions from a given algo (where algo is an aglo name, and pos is the output of a.getPos())
# this function is depreciated, replaced by check2sells
def check2sell(algo, pos):
  global triggeredStocks
  for e in pos:
    if(e['symbol'] in posList[algo] and posList[algo][e['symbol']]['sharesHeld']>0):
      print(f"{algo}\t{int(posList[algo][e['symbol']]['sharesHeld'])}\t{e['symbol']}\t{FAIL if round(float(e['unrealized_plpc'])+1,2)<1 else OKGREEN}{round(float(e['unrealized_plpc'])+1,2)}{ENDC}\t\t{FAIL if round(float(e['unrealized_intraday_plpc'])+1,2)<1 else OKGREEN}{round(float(e['unrealized_intraday_plpc'])+1,2)}{ENDC}\t\t{posList[algo][e['symbol']]['note']}")

      if(posList[algo][e['symbol']]['shouldSell']): #if marked to sell, get rid of it immediately
        print(f"{e['symbol']} marked for immediate sale.")
        sell(e['symbol'],algo) #record and everything in the sell function
        
      else:
        goodSell = eval(f"{algo}.goodSell('{e['symbol']}')")
        if(goodSell):
          if(algo+"|"+e['symbol'] not in triggeredStocks):
            triggeredStocks.add(algo+"|"+e['symbol'])
          if("triggered" not in [t.getName() for t in o.threading.enumerate()]):
            triggerThread = o.threading.Thread(target=checkTriggered) #init the thread - note locking is required here
            triggerThread.setName("triggered") #set the name to the algo and stock symb
            triggerThread.start() #start the thread
          
          if(f"{algo}-{e['symbol']}" not in [t.getName() for t in o.threading.enumerate()]): #make sure that the thread isn't already running
            triggerThread = o.threading.Thread(target=triggeredUp, args=(e['symbol'],algo)) #init the thread - note locking is required here
            triggerThread.setName(f"{algo}-{e['symbol']}") #set the name to the algo and stock symb
            triggerThread.start() #start the thread
'''


def check2buy(algo, cashAvailable, stocks2buy, verbose=False):
    global posList, cashList
    if(verbose):
        print(stocks2buy)
    random.shuffle(stocks2buy)  # shuffle the stocks2buy to avoid front loading
    # calculate the cash to be put towards various stocks in the algo (shouldn't be more than the cash available, but shouldn't be less than than the minDolPerStock (unless mindol > cashAvail))
    if(len(stocks2buy) > 0):
        cashPerStock = min(cashAvailable, max(
            float(c['account params']['minDolPerStock']), cashAvailable/len(stocks2buy)))
        if(verbose):
            print(
                f"stocks to buy for {algo}: {len(stocks2buy)}\tcash available for {algo}: {round(cashAvailable,2)}\tcash per stock: {round(cashPerStock,2)}")
    else:
        print(f"No stocks to buy for {algo}")
    # loop through the stocks to be bought
    for stock in stocks2buy:
        if(not exitFlag):  # ensure that the exitFlag is not set
            # populate the information about the stock (either from the posList if it's present, else with default info)
            stockInfo = posList[algo][stock] if stock in posList[algo] else {
                "sharesHeld": 0,
                "lastTradeDate": "NA",
                "lastTradeType": "NA",
                "buyPrice": 0,
                "shouldSell": False,
                "note": ""
            }

            # get the last date it was traded, if it isn't populated, just set it to yesterday
            try:
                lastTradeDate = dt.datetime.strptime(
                    stockInfo[algo][stock]['lastTradeDate'], "%Y-%m-%d").date()
            except Exception:
                lastTradeDate = dt.date.today()-dt.timedelta(1)

            # to avoid day trading, make sure that it either didn't trade yet today, or if it has, that it hasn't sold yet
            if lastTradeDate < dt.date.today() and stockInfo['lastTradeType'] != "sell":
                inf = o.getInfo(stock, ['price', 'mktcap'])
                [curPrice, mktCap] = [inf['price'], inf['mktcap']]
                # set number of shares to be at most some % of the mktcap, otherwise as many int shares as cash is available (or 0 if curPrice is 0)
                if(curPrice > 0):
                    shares = int(min(cashPerStock/curPrice, (mktCap/curPrice)
                                 * float(c['account params']['maxVolPerc'])))
                else:
                    shares = 0

                # print(mktCap,curPrice)
                #print(mktCap/curPrice,c['account params']['maxVolPerc'])
                #print(cashPerStock/curPrice,(mktCap/curPrice)*float(c['account params']['maxVolPerc']))

                if(verbose):
                    print(
                        f"{algo} - {stock} - {curPrice} - ok to buy {shares} shares")
                if(shares > 0):  # cannot place an order for 0 shares
                    # market must be open in order to place the trade (this check is here in the event that the program is suspended while market open, then restarted while market closed)
                    # if(o.marketIsOpen()): #TODO: add once this is confirmed, otherwise wait for a better solution to not need queries
                    isBought = buy(shares, stock, algo,
                                   curPrice)  # buy the stock
                    if(isBought):
                        print(
                            f"buy\t{shares}\t{stock}\t{algo}\t{round(curPrice,2)}\t{round(shares*curPrice,2)}")
                    else:
                        print(f"could not buy {stock}")



def checkTriggered(verbose=False):
    global triggeredStocks
    lock = o.threading.Lock()
    maxPrices = {}
    while(len(list(triggeredStocks)) > 0 and not exitFlag):  # only run if there's stocks to sell
        if(verbose):
            print(f"{len(list(triggeredStocks))} stocks triggered for sale")
        # get prices for all stocks to sell
        prices = o.getPrices(
            [e.split("|")[1]+"|stocks" for e in list(triggeredStocks)])
        maxPrices = {e: max(maxPrices[e], prices[e]['price']) if(
            e in maxPrices) else prices[e]['price'] for e in prices}  # get the max prices of the stocks since watching
        # check for stocks in triggeredStocks that aren't in prices (some error occured that we hold it but it can't be traded)
        lock.acquire()
        for e in [e for e in list(triggeredStocks) if (e.split("|")[1]+"|stocks").upper() not in prices]:
            triggeredStocks.discard(e)
        lock.release()

        print()

        for e in list(triggeredStocks):
            # get the sellUpDn % - TODO: this should probably be moved out of this for loop and generate a dict {algo:sellUpDn} since it doesn't depend on the individual stock (this would reduce function calls)
            sellUpDn = eval(f"{e.split('|')[0]}.sellUpDn()")
            # get the current prices of the stocks
            curPrice = prices[(e.split("|")[1]+'|stocks').upper()]['price']
            if(curPrice > 0):  # make sure that the price is valid
                # sell once the current price drops below some % of the maxPrice since watching or within one minute of close
                if(curPrice >= sellUpDn*maxPrices[(e.split('|')[1]+"|stocks").upper()] and (closeTime-dt.datetime.now()).total_seconds() > 60):
                    print(
                        f"{e.split('|')[0]}\t{e.split('|')[1]}\t{round(curPrice/maxPrices[(e.split('|')[1]+'|stocks').upper()],2)} : {sellUpDn}")
                else:
                    sell(e.split("|")[1], e.split("|")[0])
            else:
                print(f"{e} current price is $0. Selling")
                sell(e.split("|")[1], e.split("|")[0])
        print()
        # wait at least 5 seconds between checks, and if there are more, wait longer
        time.sleep(max(5, len(list(triggeredStocks))/5))





def check2sells(pos, verbose=False):
    global triggeredStocks
    # determine if the stocks in the algo are good sells (should return as a dict of {symb:goodSell(t/f)})
    for algo in posList:
        if(verbose):
            print(algo)
        # only the stocks in both posList[algo] and held positions
        algoSymbs = [e for e in pos if e['symbol'] in posList[algo]]
        symbList = [e['symbol'] for e in algoSymbs]  # isolate just the symbols
        # TODO: in each algo, add an error report if there's a stock that doesn't appear to be tradable (that is, it's in symbList but doesn't show up in getPrices)
        # get whether the stocks are good sells or not
        gs = eval(f"{algo}.goodSells(symbList)")
        for e in algoSymbs:  # go through the stocks of the algo
            # only display/sell if not bought today
            if(posList[algo][e['symbol']]['lastTradeDate'] < str(dt.date.today()) or posList[algo][e['symbol']]['lastTradeType'] != 'buy'):
                print(f"{algo}\t{int(posList[algo][e['symbol']]['sharesHeld'])}\t{e['symbol']}\t{FAIL if round(float(e['unrealized_plpc'])+1,2)<1 else OKGREEN}{round(float(e['unrealized_plpc'])+1,2)}{ENDC}\t\t{FAIL if round(float(e['unrealized_intraday_plpc'])+1,2)<1 else OKGREEN}{round(float(e['unrealized_intraday_plpc'])+1,2)}{ENDC}\t\t"+str(
                    round(eval(f'{algo}.sellDn("{e["symbol"]}")'), 2))+" & "+str(round(eval(f'{algo}.sellUp("{e["symbol"]}")'), 2))+f"\t{posList[algo][e['symbol']]['note']}")
                # ensure that the market is open in order to actually place a trade
                # this check is here in the event that the program is suspended while open, then restarted while closed
                # if(o.marketIsOpen()): #TODO: confirm that this is needed first and not a setting that can be changed outside of this script
                if(gs[e['symbol']] == 1):  # if the stock is a good sell (sellUp)
                    # make sure that it's not already present
                    if(algo+"|"+e['symbol'] not in triggeredStocks):
                        # if not, then add it to the triggered list
                        triggeredStocks.add(algo+"|"+e['symbol'])
                    # make sure that the triggered list isn't already running
                    if("triggered" not in [t.getName() for t in o.threading.enumerate()]):
                        # init the thread - note locking is required here
                        triggerThread = o.threading.Thread(
                            target=checkTriggered)
                        # set the name to the algo and stock symb
                        triggerThread.setName("triggered")
                        triggerThread.start()  # start the thread
                elif(gs[e['symbol']] == -1):  # else if it sells down (stop-loss)
                    # sell immediately
                    sell(e['symbol'], algo)



def sell(stock, algo):
    global posList, cashList, triggeredStocks
    if(posList[algo][stock]['sharesHeld'] > 0):
        # print(f"{algo} - {stock} - {posList[algo][stock]['sharesHeld']} shares")
        pass
        
        # TODO: call robinhood api here.
        # r = a.createOrder("sell", float(
        #     posList[algo][stock]['sharesHeld']), stock)
    else:
        print(f"No shares held of {stock}")
        triggeredStocks.discard(algo+"|"+stock)
        return False

    # TODO: this is an incorrect check
    # see how it looks in here: https://alpaca.markets/docs/trading-on-alpaca/orders/#order-lifecycle
    # if('status' in r and r['status'] == "accepted"):  # check that it actually sold
    #     lock = o.threading.Lock()
    #     lock.acquire()
    #     # update the cash earned by the sale
    #     cashList[algo]['earned'] += o.getInfo(stock)['price'] * \
    #         posList[algo][stock]["sharesHeld"]
    #     posList[algo][stock] = {  # update the entry in posList
    #         "sharesHeld": 0,
    #         "lastTradeDate": str(dt.date.today()),
    #         "lastTradeType": "sell",
    #         "buyPrice": 0,
    #         "shouldSell": False,
    #         "note": ""
    #     }

    #     open(c['file locations']['posList'], 'w').write(json.dumps(
    #         {'algos': posList, 'cash': cashList}, indent=2))  # update the posList file
    #     triggeredStocks.discard(algo+"|"+stock)
    #     lock.release()
    #     print(f"Sold {algo}'s shares of {stock}")
    #     return True
    # else:
    #     print(
    #         f"Order to sell {posList[algo][stock]['sharesHeld']} shares of {stock} for {algo} not accepted")
    #     return False



def buy(shares, stock, algo, buyPrice):
    # this needs to happen first so that it can be as accurate as possible
    print("Buying", shares, "shares of", stock, "at", buyPrice)
    return False
    # r = a.createOrder("buy", shares, stock)
    # global posList, cashList

    # # check to make sure that it actually bought - TODO: does the presence of 'status' indicate that it bought or not?
    # if('status' in r and r['status'] == "accepted"):
    #     lock = o.threading.Lock()
    #     lock.acquire()
    #     posList[algo][stock] = {  # update the entry in posList
    #         "sharesHeld": float(posList[algo][stock]['sharesHeld'])+float(r['qty']) if stock in posList[algo] else float(r['qty']),
    #         "lastTradeDate": str(dt.date.today()),
    #         "lastTradeType": "buy",
    #         # running avg = (prevAvg*n+newAvg*m)/(n+m)
    #         "buyPrice": (posList[algo][stock]['buyPrice']*posList[algo][stock]['sharesHeld']+buyPrice*float(r['qty']))/(posList[algo][stock]['sharesHeld']+float(r['qty'])) if stock in posList[algo] else buyPrice,
    #         "shouldSell": False,
    #         "note": algoList[algo][stock] if stock in algoList[algo] else ""
    #     }

    #     cashList[algo]['invested'] += buyPrice*shares
    #     open(c['file locations']['posList'], 'w').write(json.dumps(
    #         {'algos': posList, 'cash': cashList}, indent=2))  # update posList file
    #     lock.release()
    #     return True
    # else:  # it didn't actually buy
    #     print(f"Order to buy {shares} shares of {stock} not accepted")
    #     return False




def setPosList(algoList, verbose=True):
    posList = {}
    cashList = {}
    # if the posList file doesn't exist
    if(not os.path.isfile(c['file locations']['posList'])):
        if(verbose):
            print("File is missing. Creating and adding blank lists...")
        lock = o.threading.Lock()
        lock.acquire()
        with open(c['file locations']['posList'], 'w') as f:
            # write a empty algos and 0 cash for all algos to the posList file
            f.write(json.dumps({'algos': {e: {} for e in algoList}, 'cash': {
                    e: {"earned": 0, "invested": 0} for e in algoList}}))
        # lists is the data directly from the posList file
        lists = json.loads(open(c['file locations']['posList'], 'r').read())
        # posList contains only the positions
        posList = lists['algos']
        # cashList contains only the cash
        cashList = lists['cash']
        lock.release()
    else:  # if it does exist
        # try: #try reading any json data from it
        lock = o.threading.Lock()
        lock.acquire()
        with open(c['file locations']['posList'], 'r') as f:
            lists = json.loads(f.read())

        posList = lists['algos']
        cashList = lists['cash']

        # algos that are being used but not in the posList
        missingAlgos = [algo for algo in algoList if algo not in posList]
        for algo in missingAlgos:
            if(verbose):
                print(f"Adding {algo} to posList")
            posList[algo] = {}

        missingCash = [algo for algo in algoList if algo not in cashList]
        for algo in missingCash:
            if(verbose):
                print(f"Adding {algo} to cashList")
            cashList[algo] = {'earned': 0, 'invested': 0}

        lock.release()

        # write the missing algos to the file
        lock = o.threading.Lock()
        lock.acquire()
        with open(c['file locations']['posList'], 'w') as f:
            f.write(json.dumps({'algos': posList, 'cash': cashList}))
        lock.release()
        '''
    except Exception: #if it fails, then just write the empty algoList to the file
      #TODO: this is dangerous! This could potentially overwrite all saved position data if there's any error above. TODO Make this more robust
      if(verbose): print("Something went wrong. Overwriting poslist file")
      lock = o.threading.Lock()
      lock.acquire()
      with open(c['file locations']['posList'],'w') as f:
        f.write(json.dumps({'algos':{e:{} for e in algoList},'cash':{e:{"earned":0,"invested":0} for e in algoList}})) #write a empty algos and 0 cash for all algos to the posList file
      lists = json.loads(open(c['file locations']['posList'],'r').read())
      posList = lists['algos']
      cashList = lists['cash']
      lock.release()
    '''
    return [posList, cashList]



def syncPosList(verbose=False):
    global posList, cashList
    # locking is needed to write to the file and edit the posList var (will have to see how threads and globals work with each other)
    lock = o.threading.Lock()
    print("Syncing posList...")

    # check if an algo in the posList is removed from the algoList
    for inactiveAlgo in [algo for algo in posList if algo not in algoList]:
        if(verbose):
            print(f"Looking at inactive algo {inactiveAlgo}")
        # stocks that are in a removed algo should be moved to an active algo that has it, if none do, then move it to the active algo with the highest loss
        if(inactiveAlgo in cashList):
            if(verbose):
                print(f"Removing {inactiveAlgo} from cashList")
            cashList.pop(inactiveAlgo, None)

        # move the stocks from the inactive algo to active ones
        for symb in posList[inactiveAlgo]:  # stocks in the removed algo
            # get all active algos that contain it
            activeAlgosWithStock = [
                e for e in posList if(e in algoList and symb in e)]
            maxAlgo = ['x', 0]  # algo and the max gain of the stock
            # get the algo with the max gain for this stock
            if(len(activeAlgosWithStock) > 0):  # if there's at least 1 active algo that contains it
                for activeAlgo in activeAlgosWithStock:  # look thru each algo that could hold the stock
                    # find the sell up of that algo
                    sellUp = eval(f"{activeAlgo}.sellUp('{symb}')")
                    # get the greater of the two algos
                    maxAlgo = [activeAlgo,
                               sellUp] if sellUp > maxAlgo[1] else maxAlgo
            else:  # if there are not active algos that contain it
                for activeAlgo in algoList:  # then loop through all active algos
                    # find the sell up of that algo
                    sellUp = eval(f"{activeAlgo}.sellUp('{symb}')")
                    # get the greater of the two algos
                    maxAlgo = [activeAlgo,
                               sellUp] if sellUp > maxAlgo[1] else maxAlgo

            if(verbose):
                print(
                    f"{inactiveAlgo} algo is inactive. Moving {symb} from {inactiveAlgo} to {maxAlgo[0]}")

            lock.acquire()
            try:  # this should evaluate if the symb is already present in the active algo
                # only transfer over the shares active algo data is more important
                posList[maxAlgo[0]][symb]['sharesHeld'] += posList[inactiveAlgo][symb]['sharesHeld']
            except Exception:  # this should evaluate if the symb is not already present in the active algo
                posList[maxAlgo[0]][symb] = {  # transfer over all data from the inactive one
                    'sharesHeld': posList[inactiveAlgo][symb]['sharesHeld'],
                    'lastTradeDate': posList[inactiveAlgo][symb]['lastTradeDate'],
                    'lastTradeType': posList[inactiveAlgo][symb]['lastTradeType'],
                    'buyPrice': posList[inactiveAlgo][symb]['buyPrice'],
                    'shouldSell': posList[inactiveAlgo][symb]['shouldSell'],
                    'note': posList[inactiveAlgo][symb]['note']
                }

            # remove the shares fromt he inactive algo
            posList[inactiveAlgo][symb]['sharesHeld'] = 0
            lock.release()

        del posList[inactiveAlgo]  # remove the inactive algo from the

    if(verbose):
        print("getting actually held positions")
    p = a.getPos()
    heldPos = {e['symbol']: float(e['qty'])
               for e in p}  # actually held positions
    # get the actual buy prices for each stock
    heldBuyPrices = {e['symbol']: float(e['avg_entry_price']) for e in p}

    if(verbose):
        print("Adding any missing fields to current records")
    for algo in posList:
        for symb in posList[algo]:
            lock.acquire()
            if('sharesHeld' not in posList[algo][symb]):
                if(verbose):
                    print(f"{algo} {symb} missing sharesHeld")
                posList[algo][symb]['sharesHeld'] = 0
            if('lastTradeDate' not in posList[algo][symb]):
                if(verbose):
                    print(f"{algo} {symb} missing lastTradeDate")
                posList[algo][symb]['lastTradeDate'] = "NA"
            if('lastTradeType' not in posList[algo][symb]):
                if(verbose):
                    print(f"{algo} {symb} missing lastTradeType")
                posList[algo][symb]['lastTradeType'] = "NA"
            if('buyPrice' not in posList[algo][symb]):
                if(verbose):
                    print(f"{algo} {symb} missing buyPrice")
                posList[algo][symb]['buyPrice'] = heldBuyPrices[symb] if symb in heldBuyPrices else 0
            if('shouldSell' not in posList[algo][symb]):
                if(verbose):
                    print(f"{algo} {symb} missing shouldSell")
                posList[algo][symb]['shouldSell'] = False
            if('note' not in posList[algo][symb]):
                if(verbose):
                    print(f"{algo} {symb} missing note")
                posList[algo][symb]['note'] = algoList[algo][symb] if(
                    algo in algoList and symb in algoList[algo]) else ""
            lock.release()

    # total stocks in posList
    if(verbose):
        print("getting recorded positions...")
    recPos = {}  # recorded positions
    for algo in posList:  # for every algo in the posList
        if(len(posList) > 0):
            for stock in posList[algo]:  # for every stock in that algo
                if stock not in recPos:  # if that stock isn't already in the recorded positions
                    recPos[stock] = float(
                        posList[algo][stock]['sharesHeld'])  # add it
                else:
                    # add the shares held
                    recPos[stock] += float(posList[algo][stock]['sharesHeld'])

    if(not eq(recPos, heldPos)):
        if(verbose):
            print("discrepency found between records and actuals")
        # if there are any stocks recorded that aren't in the heldPos, remove them
        # if there are an excess of shares in the recPos than the heldPos, look for any in the algos that match the disparity, and remove them from that algo
           # if none match (i.e. heldPos and recPos both have a stock, but there's an unknown amount extra in recPos), then just sell it all

        # if there are any stocks in heldPos that aren't recorded, then compare to algoList
           # if it's in algolist, assign to all algos that have it, else assign to algo with the smallest gain to offload it asap
        # if there are an excess of shares in the heldPos than the recPos, then add the excess to the algo with the highest gain to increase gains as much as possible

        # compare recPos to heldPos

        # if there are any stocks recorded that aren't in the heldPos, remove them
        # for all stocks in recorded and not in heldPos
        for symb in [s for s in recPos if s not in heldPos]:
            for algo in posList:  # check every algo
                if(verbose):
                    print(
                        f"{symb} not found in actuals. Removing from {algo} records")
                lock.acquire()
                posList[algo].pop(symb, None)  # remove from posList
                lock.release()
            recPos.pop(symb, None)  # remove from recorded

        # for each stock, if there are an excess of shares in the recPos than the heldPos, look for any in the algos that match the disparity, and remove them from that algo
            # if none match (i.e. heldPos and recPos both have a stock, but there's an unknown amount extra in recPos), then trim off the amount extra from the algo that has the most above the disparity
            # if no algo has any above it: then sell the whole lot TODO: this should probably be handled differently, but it's some complexity that can be saved for later
        # for all stocks where the recorded is greater than the held
        for symb in [s for s in recPos if recPos[s] > heldPos[s]]:
            for algo in posList:  # for every algo
                # remove any that may be exact matches
                if(symb in posList[algo] and float(posList[algo][symb]['sharesHeld']) == recPos[symb]-heldPos[symb]):
                    if(verbose):
                        print(
                            f"Removing {float(posList[algo][symb]['sharesHeld'])} shares of {symb} from {algo} records")
                    recPos[symb] -= float(posList[algo][symb]['sharesHeld'])
                    if(recPos[symb] == 0):
                        recPos.pop(symb, None)
                    lock.acquire()
                    posList[algo].pop(symb, None)
                    lock.release()

            # if there's still a discrepency (ie. there is not an exact difference)
            if(recPos[symb] > heldPos[symb]):  # if the recorded still has more than the held
                # get algos with the symbol and the number of shares of that symbol
                if(verbose):
                    print(f"more shares of {symb} in records than actuals")
                # get the number of shares per algo if the algo has the stock
                algosWithStock = {e: float(
                    posList[e][symb]['sharesHeld']) for e in posList if symb in posList[e]}
                for algo in algosWithStock:
                    # TODO: this should probably be changed to spread out over multiple algos rather than just 1
                    # if an algo has more than the disparity
                    if(algosWithStock[algo] >= recPos[symb]-heldPos[symb]):
                        if(verbose):
                            print(
                                f"{algo} has {algosWithStock[algo]} shares of {symb}. Removing {recPos[symb]-heldPos[symb]} shares")
                        lock.acquire()
                        posList[algo][symb]['sharesHeld'] -= recPos[symb] - \
                            heldPos[symb]  # remove the disparity
                        lock.release()
                        recPos[symb] -= recPos[symb]-heldPos[symb]
                        break

                # if the disparity wasn't caught, then just sell the lot
                if(recPos[symb] > heldPos[symb]):
                    print(
                        f"Could not find a suitable sync for {symb}. Selling the lot.")
                    for algo in [algo for algo in posList if symb in posList[algo]]:
                        print(f"{algo} has {posList[algo][symb]['sharesHeld']} shares of {symb}")
                        sell(symb, algo)

        # compare heldPos to recPos

        # ensure algoList is up to date
    # compare again after the initial comparison
    if(not eq(recPos, heldPos) or not os.path.isfile(c['file locations']['buyList'])):
        if(verbose):
            print(
                f"Discrepency still present or buyList file is missing. Updating buy list")
        # if the lists aren't currently updating and haven't already updated today, then update
        if(not listsUpdatedToday and len([t for t in o.threading.enumerate() if t.getName().startswith('update')]) == 0):
            # init the thread - note locking is required here
            updateListsThread = o.threading.Thread(target=updateLists)
            # set the name to the stock symb
            updateListsThread.setName('updateLists')
            updateListsThread.start()  # start the thread

        if(verbose):
            print("Waiting for stock lists to finish updating...")
        # wait for the lists to finish updating
        while(not listsUpdatedToday or len([t for t in o.threading.enumerate() if t.getName().startswith('update')]) > 0):
            # print([t.getName() for t in o.threading.enumerate() if t.getName().startswith('update')])
            time.sleep(2)
        if(verbose):
            print("lists done updating for syncPosList")

        # check that symb is somewhere in algoList
        # if it is, then add it to the algo that has it with the highest gain
        # else append it to the algo with the smallest gain
        # for all stocks actually held and not recorded
        for symb in [s for s in heldPos if s not in recPos]:

            # try and find a home for a stock by looking in the stocks to be bought (get all algos that may have it)
            algosWithStock = [e for e in algoList if symb in algoList[e]]
            if(len(algosWithStock) > 0):  # if an algo has it
                maxAlgo = ['x', 0]  # algo and the max gain of the stock
                # get the algo with the max gain for this stock
                for algo in algosWithStock:  # look thru each algo that could hold the stock, and give it to the one with the most gain potential
                    # find the sell up of that algo
                    sellUp = eval(f"{algo}.sellUp('{symb}')")
                    # get the greater of the two algos
                    maxAlgo = [
                        algo, sellUp] if sellUp > maxAlgo[1] else maxAlgo
                if(verbose):
                    print(
                        f"Adding {heldPos[symb]} shares of {symb} to {maxAlgo[0]}.")
                lock.acquire()
                posList[maxAlgo[0]][symb] = {'lastTradeDate': 'NA',
                                             'lastTradeType': 'NA',
                                             'sharesHeld': heldPos[symb],
                                             'shouldSell': False,
                                             'buyPrice': heldBuyPrices[symb],
                                             'note': algoList[maxAlgo[0]][symb]
                                             }
                lock.release()
                # also add the stock to the recPos temp var
                recPos[symb] = heldPos[symb]

            else:  # if no algo has it, give it to the algo with the least amount of loss
                # algo and the acceptable loss of the stock
                minAlgo = ['x', 100]
                for algo in algoList:  # for every algo that'll potentially gain
                    # get the sell dn of each algo
                    sellUp = eval(f"{algo}.sellUp('{symb}')")
                    # get the greater of the the two algos
                    minAlgo = [
                        algo, sellUp] if sellUp < minAlgo[1] else minAlgo
                # add to the algo with the least gain (to get rid of asap)
                if(verbose):
                    print(
                        f"No algo found to have {symb}. Adding {heldPos[symb]} shares to {minAlgo[0]}.")
                lock.acquire()
                posList[minAlgo[0]][symb] = {'lastTradeDate': 'NA',
                                             'lastTradeType': 'NA',
                                             'sharesHeld': heldPos[symb],
                                             'buyPrice': heldBuyPrices[symb],
                                             'shouldSell': False,
                                             'note': algoList[minAlgo[0]][symb] if symb in algoList[minAlgo[0]] else ""
                                             }
                lock.release()
                # also add the stock to the recPos temp var
                recPos[symb] = heldPos[symb]

        # find symbols that have more actual shares than recorded shares
        # add the shares to the algo with the highest gain
        # for all stocks where the actual is greater than the recorded
        for symb in [s for s in heldPos if heldPos[s] > recPos[s]]:
            # get all currently used algos holding the stock
            algosWithStock = [
                e for e in posList if symb in posList[e] and e in algoList]

            # init maxAlgo to the first algo in the list
            maxAlgo = algosWithStock[0]
            # get the algo with the max gain potential and ensure that the symb is in the algo (skip the first one since it's the init value - save a loop)
            for algo in algosWithStock[1:]:
                maxAlgo = algo if eval(f"{algo}.sellUp(symb)") > eval(
                    f"{maxAlgo}.sellUp('{symb}')") else maxAlgo  # get the algo with the largest sellUp value

            lock.acquire()
            posList[maxAlgo][symb]['sharesHeld'] += heldPos[symb] - \
                recPos[symb]  # add in the disparity
            lock.release()

    # remove any symbs that have 0 shares, remove any algos that have 0 symbs
    if(verbose):
        print("Removing blanks")
    for algo in list(posList):
        # must be cast as list in order to not change dict size (this makes a copy)
        for symb in list(posList[algo]):
            if(posList[algo][symb]['sharesHeld'] == 0):
                lock.acquire()
                posList[algo].pop(symb, None)
                lock.release()
        # remove any algos that aren't in the algoList and have 0 symbs in them
        if(algo not in algoList and len(posList[algo]) == 0):
            lock.acquire()
            posList.pop(algo, None)
            lock.release()

    for algo in posList:
        if(verbose):
            print(f"Calculating invested amount in {algo}... ", end="")
        cashList[algo]['invested'] = sum(
            [posList[algo][s]['sharesHeld']*posList[algo][s]['buyPrice'] for s in posList[algo]])
        if(verbose):
            print(round(cashList[algo]['invested'], 2))

    if(verbose):
        print("Marking to be sold")
    revSplits = o.reverseSplitters()
    for algo in posList:
        for symb in posList[algo]:
            if(symb in revSplits):
                if(verbose):
                    print(f"{algo} - {symb} marked for sale")
                lock.acquire()
                posList[algo][symb]['shouldSell'] = True
                lock.release()

    # write to the file
    lock.acquire()
    with open(c['file locations']['posList'], 'w') as f:
        if(verbose):
            print("Writing to posList file")
        f.write(json.dumps({'algos': posList, 'cash': cashList}, indent=2))
    lock.release()
    print("Done syncing posList")








# run the main function
if __name__ == '__main__':
    global exitFlag
    exitFlag = False  # set to true if the program stopped by ctrl+c

    try:
        main(False)  # start running the program
    except KeyboardInterrupt:  # exit on ctrl+c
        print("Exiting")
        exitFlag = True

    except Exception:  # record unhandled exceptions
        print("An unhandled error was encountered. Please check the log.")
        traceback.print_exc(file=open(c['file locations']['errLog'], "a"))
