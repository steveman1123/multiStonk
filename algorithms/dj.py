# this file contains functions specifically for the double jump (aka dead cat bounce) algo
# when a penny stock gains a significant amount with a large volume then falls with a small volume, then it generally gains a second time
import _multistonks.otherfxns as o
import robin_account 

# name of the algo based on the file name
algo = o.os.path.basename(__file__).split('.')[0]


def init(configFile):
    global posList, c
    # set the multi config file
    # TODO: add error if the file doesn't exist.
    # TODO: in otherfxns, from configparser import ConfigParser (since I don't think we use anthing else)
    c = o.configparser.ConfigParser()
    c.read(configFile)

    # stocks held by this algo according to the records
    lock = o.threading.Lock()
    lock.acquire()
    posList = o.json.loads(open(c['file locations']['posList'], 'r').read())[
        'algos'][algo]
    lock.release()

# get a list of potential gainers according to this algo


def getList(verbose=True):
    if(verbose):
        print(f"getting unsorted list for {algo}...")
    ul = getUnsortedList()
    if(verbose):
        print(f"found {len(ul)} stocks to sort through for {algo}.")
        # print(f"determining buys for {algo}: stocks.\t {symbList}")

    if(verbose):
        print(f"finding stocks for {algo}...")
    # get dict of the list of stocks if they're good buys or not
    gb = goodBuys(ul)
    # print(gb)
    
    # the only time that the first char is a number is if it is a valid/good buy
    gb = {e: gb[e] for e in gb if gb[e][0].isnumeric()}
    if(verbose):
        print(f"{len(gb)} found for {algo}.")
    return gb

# TODO: add verbose-ness to goodBuys, goodSells

# checks whether something is a good buy or not (if not, return why - no initial jump or second jump already missed).
# if it is a good buy, return initial jump date
# this is where the magic really happens
# this function is depreciated, replaced by goodBuys


def goodBuy(symb, days2look=-1, verbose=False):  # days2look=how far back to look for a jump
    if(days2look < 0):
        days2look = int(c[algo]['simDays2look'])
    validBuy = "not tradable"  # set to the jump date if it's valid
    if(o.getInfo(symb, ['istradable'])['istradable']):
        # calc price % diff over past 20 days (current price/price of day n) - current must be >= 80% for any
        # calc volume % diff over average past some days (~60 days?) - must be sufficiently higher (~300% higher?)

        # wait for stock price to fall for this many days
        days2wait4fall = int(c[algo]['simWait4fall'])
        # add 1 to account for the jump day itself
        startDate = days2wait4fall + int(c[algo]['simStartDateDiff'])
        # stock first must jump by this amount (1.3=130% over 1 day)
        firstJumpAmt = float(c[algo]['simFirstJumpAmt'])
        sellUp = float(c[algo]['simSellUp'])  # % to sell up at
        sellDn = float(c[algo]['simSellDn'])  # % to sell dn at

        # make sure that the jump happened in the  frame rather than too long ago
        # arbitrary number to avg volumes over
        volAvgDays = int(c[algo]['simVolAvgDays'])
        # check if the price jumped suo.bstantially over the last __ trade days
        checkPriceDays = int(c[algo]['simChkPriceDays'])
        # check if the price jumped by this amount in the above days (% - i.e 1.5 = 150%)
        checkPriceAmt = float(c[algo]['simChkPriceAmt'])
        # check if the volume increased by this amount during the jump (i.e. 3 = 300% or 3x, 0.5 = 50% or 0.5x)
        volGain = float(c[algo]['simVolGain'])
        # check if the volume decreases by this amount during the price drop
        volLoss = float(c[algo]['simVolLoss'])
        # price should drop this far when the volume drops
        priceDrop = float(c[algo]['simPriceDrop'])

        start = str(o.dt.date.today() -
                    o.dt.timedelta(days=(volAvgDays+days2look)))
        end = str(o.dt.date.today())

        dateData = o.getHistory(symb, start, end)

        if(startDate >= len(dateData)-2):  # if a stock returns nothing or very few data pts
            validBuy = "Few data points available"
        else:
            validBuy = "initial jump not found"
            while(startDate < min(days2look, len(dateData)-2) and float(dateData[startDate][1])/float(dateData[startDate+1][1]) < firstJumpAmt):
                startDate += 1

                # if the price has jumped sufficiently for the first time
                if(float(dateData[startDate][1])/float(dateData[startDate+1][1]) >= firstJumpAmt):

                    avgVol = sum([int(dateData[i][2]) for i in range(startDate, min(
                        startDate+volAvgDays, len(dateData)))])/volAvgDays  # avg of volumes over a few days

                    lastVol = int(dateData[startDate][2])  # the latest volume
                    # the latest highest price
                    lastPrice = float(dateData[startDate][4])

                    if(lastVol/avgVol > volGain):  # much larger than normal volume
                        # volume had to have gained
                        # if the next day's price has fallen significantly and the volume has also fallen
                        if(float(dateData[startDate-days2wait4fall][4])/lastPrice-1 < priceDrop and int(dateData[startDate-days2wait4fall][2]) <= lastVol*volLoss):
                            # the jump happened, the volume gained, the next day's price and volumes have fallen
                            dayPrice = lastPrice
                            i = 1  # increment through days looking for a jump - start with 1 day before startDate
                            # check within the the last few days, check the price has risen compared to the past some days, and we're within the valid timeframe
                            while(i <= checkPriceDays and lastPrice/dayPrice < checkPriceAmt and startDate+i < len(dateData)):
                                dayPrice = float(dateData[startDate+i][4])
                                i += 1

                            # TODO: read through this logic some more to determine where exactly to put sellDn
                            if(lastPrice/dayPrice >= checkPriceAmt):
                                # the price jumped compared to both the previous day and to the past few days, the volume gained, and the price and the volume both fell
                                # check to see if we missed the next jump (where we want to strike)
                                missedJump = False
                                validBuy = "Missed jump"
                                # history grabs from previous day and before, it does not grab today's info. Check that it hasn't jumped today too (only query once since it's really not important)
                                if(not o.jumpedToday(symb, sellUp, maxTries=1)):
                                    for e in range(0, startDate):
                                        if(verbose):
                                            print(str(dateData[e])+" - "+str(float(dateData[e][4])/float(
                                                dateData[e+1][1])) + " - " + str(sellUp))
                                        # compare the high vs previous close
                                        if(float(dateData[e][4])/float(dateData[e+1][1]) >= sellUp):
                                            missedJump = True
                                    if(not missedJump):
                                        if(verbose):
                                            print(algo, symb)
                                        # return the date the stock initially jumped
                                        validBuy = dateData[startDate][0]

    if(verbose):
        print(symb, validBuy)
    return validBuy


# perform the same checks as goodBuy but multiplexed for fewer requests
# returns a dict of {symb:validBuyText} where validBuyText will contain the failure reason or if it succeeds, then it is the initial jump date
def goodBuys(symbList, days2look=-1, verbose=False):
    if(days2look < 0):
        days2look = int(c[algo]['simDays2look'])
    # calc price % diff over past 20 days (current price/price of day n) - current must be >= 80% for any
    # calc volume % diff over average past some days (~60 days?) - must be sufficiently higher (~300% higher?)

    # wait for stock price to fall for this many days
    days2wait4fall = int(c[algo]['simWait4fall'])
    # stock first must jump by this amount (1.3=130% over 1 day)
    firstJumpAmt = float(c[algo]['simFirstJumpAmt'])
    sellUp = float(c[algo]['simSellUp'])  # % to sell up at
    sellDn = float(c[algo]['simSellDn'])  # % to sell dn at

    # make sure that the jump happened in the  frame rather than too long ago
    # arbitrary number to avg volumes over
    volAvgDays = int(c[algo]['simVolAvgDays'])
    # check if the price jumped substantially over the last __ trade days
    checkPriceDays = int(c[algo]['simChkPriceDays'])
    # check if the price jumped by this amount in the above days (% - i.e 1.5 = 150%)
    checkPriceAmt = float(c[algo]['simChkPriceAmt'])
    # check if the volume increased by this amount during the jump (i.e. 3 = 300% or 3x, 0.5 = 50% or 0.5x)
    volGain = float(c[algo]['simVolGain'])
    # check if the volume decreases by this amount during the price drop
    volLoss = float(c[algo]['simVolLoss'])
    # price should drop this far when the volume drops
    priceDrop = float(c[algo]['simPriceDrop'])

    start = str(o.dt.date.today()-o.dt.timedelta(days=(volAvgDays+days2look)))
    end = str(o.dt.date.today())

    # get the vol, current and opening prices of all valid stocks (invalid ones will not be returned by getPrices) - using as a filter to get rid of not tradable stocks
    # prices = o.getPrices([e+"|stocks" for e in symbList])
    prices = robin_account.getPrices([s for s in symbList])

    
    
    
    symbList = [e.split("|")[0]
                for e in prices]  # only look at the valid stocks

    out = {}  # data to be returned

    for symb in symbList:
        # add 1 to account for the jump day itself
        startDate = days2wait4fall + int(c[algo]['simStartDateDiff'])

        dateData = o.getHistory(symb, start, end)
        if(startDate >= len(dateData)-2):  # if a stock returns nothing or very few data pts
            validBuy = "Few data points available"
        else:
            validBuy = "initial jump not found"
            while(startDate < min(days2look, len(dateData)-2) and float(dateData[startDate][1])/float(dateData[startDate+1][1]) < firstJumpAmt):
                startDate += 1

                # if the price has jumped sufficiently for the first time
                if(float(dateData[startDate][1])/float(dateData[startDate+1][1]) >= firstJumpAmt):
                    if(verbose):
                        print(
                            f"{symb}\tinitial price jumped on {dateData[startDate][0]}")
                    avgVol = sum([int(dateData[i][2]) for i in range(startDate, min(
                        startDate+volAvgDays, len(dateData)))])/volAvgDays  # avg of volumes over a few days

                    lastVol = int(dateData[startDate][2])  # the latest volume
                    # the latest highest price
                    lastPrice = float(dateData[startDate][4])

                    if(lastVol/avgVol > volGain):  # much larger than normal volume
                        if(verbose):
                            print(f"{symb}\tvol gained")
                        # volume had to have gained
                        # if the next day's price has fallen significantly and the volume has also fallen
                        if(float(dateData[startDate-days2wait4fall][4])/lastPrice-1 < priceDrop and int(dateData[startDate-days2wait4fall][2]) <= lastVol*volLoss):
                            if(verbose):
                                print(
                                    f"{symb}\tprice and vol dropped on {dateData[startDate-days2wait4fall][0]}")
                            # the jump happened, the volume gained, the next day's price and volumes have fallen
                            dayPrice = lastPrice
                            i = 1  # increment through days looking for a jump - start with 1 day before startDate
                            # check within the the last few days, check the price has risen compared to the past some days, and we're within the valid timeframe
                            while(i <= checkPriceDays and lastPrice/dayPrice < checkPriceAmt and startDate+i < len(dateData)):
                                dayPrice = float(dateData[startDate+i][4])
                                i += 1

                            # TODO: read through this logic some more to determine where exactly to put sellDn
                            if(lastPrice/dayPrice >= checkPriceAmt):
                                if(verbose):
                                    print(f"{symb}\t")
                                # the price jumped compared to both the previous day and to the past few days, the volume gained, and the price and the volume both fell
                                # check to see if we missed the next jump (where we want to strike)
                                missedJump = False
                                validBuy = "Missed jump"
                                # history grabs from previous day and before, it does not grab today's info. Check that it hasn't jumped today too
                                if(not o.jumpedToday(symb, sellUp, maxTries=1)):
                                    for e in range(0, startDate):
                                        if(verbose):
                                            print(str(dateData[e])+" - "+str(float(dateData[e][4])/float(
                                                dateData[e+1][1])) + " - " + str(sellUp))
                                        # compare the high vs previous close
                                        if(float(dateData[e][4])/float(dateData[e+1][1]) >= sellUp):
                                            missedJump = True
                                    if(not missedJump):
                                        if(verbose):
                                            print(algo, symb)
                                        # return the date the stock initially jumped (in yyyy-mm-dd format)
                                        validBuy = str(o.dt.datetime.strptime(
                                            dateData[startDate][0], "%m/%d/%Y").date())

        if(verbose):
            print(symb+"\t"+validBuy)
        out[symb] = validBuy

    return out

# perform the same checks as goodSell but multiplexed for fewer requests
# return dict of {symb:goodSell}


def goodSells(symbList, verbose=False):  # symbList is a list of stocks ready to be sold
    lock = o.threading.Lock()
    lock.acquire()
    posList = o.json.loads(open(c['file locations']['posList'], 'r').read())[
        'algos'][algo]  # load up the stock data for the algo
    lock.release()
    # only look at the stocks that are in the algo
    symbList = [e for e in symbList if e in posList]
    buyPrices = {s: float(posList[s]['buyPrice'])
                 for s in symbList}  # get buyPrices {symb:buyPrce}
    # currently format of {symb|assetclass:{price,vol,open}}
    # prices = o.getPrices([s+"|stocks" for s in symbList])
    prices = robin_account.getPrices([s for s in symbList])
    
    # now format of {symb:{price,vol,open}}
    prices = {s.split("|")[0]: prices[s] for s in prices}

    gs = {}
    for s in symbList:
        if(s in prices):
            if(verbose):
                print(
                    f"{s}\topen: {round(prices[s]['price']/prices[s]['open'],2)}\tbuy: {round(prices[s]['price']/buyPrices[s],2)}\tsellUp: {sellUp(s)}\tsellDn: {sellDn(s)}")
            # check if price triggered up
            if(prices[s]['open'] > 0 and buyPrices[s] > 0):
                if(prices[s]['price']/prices[s]['open'] >= sellUp(s) or prices[s]['price']/buyPrices[s] >= sellUp(s)):
                    gs[s] = 1
                # check if price triggered down
                elif(prices[s]['price']/prices[s]['open'] < sellDn(s) or prices[s]['price']/buyPrices[s] < sellDn(s)):
                    gs[s] = -1
                else:  # price didn't trigger either side
                    gs[s] = 0
            else:  # TODO: is this correct? Should it sell if it can't find a price?
                gs[s] = 0
        else:
            gs[s] = 0

    # display stocks that have an error
    for e in [e for e in symbList if e not in gs]:
        print(f"{e} not tradable")

    return gs


# get list of stocks from stocksUnder1 and marketWatch lists
# TODO: should make this an otherfxns fxn with params so multiple algos can pull from the same code
# def getUnsortedList(verbose=False):
#     symbList = list()
#     marketwatch, stocksunder = robin_account.multistock_server(algo,c)    
#     symbList += marketwatch
#     symbList += stocksunder    
#     if(verbose):
#         print("Removing Duplicates...")
#     symbList = list(dict.fromkeys(symbList))  # combine and remove duplicates
#     return symbList




def getUnsortedList(verbose=True):
    symbList = list()
    buyholdsell,trending = robin_account.multistock_server(algo,c=c)
    # print(buyholdsell,trending)
    for i in buyholdsell:
        if i == "winners":
            symbList += buyholdsell[i]
        if i == "losers":
            symbList += buyholdsell[i]
    symbList += trending
    # symbList +=suggestion
    


    if(verbose):
        print("Removing Duplicates...")
    symbList = list(dict.fromkeys(symbList))  # combine and remove duplicates
    
    # print(symbList)
    return symbList

# determine if a stock is a good sell or not
# depreciated, replaced with goodSells
def goodSell(symb):
    # check if price<sellDn
    lock = o.threading.Lock()
    lock.acquire()
    stockList = o.json.loads(open(c['file locations']['posList'], 'r').read())[
        'algos'][algo]
    lock.release()
    buyPrice = float(stockList[symb]['buyPrice'])
    inf = o.getInfo(symb, ['price', 'open'])

    if(inf['open'] > 0):
        # if change since open has gone beyond sell params
        if(inf['price']/inf['open'] < sellDn(symb) or inf['price']/inf['open'] >= sellUp(symb)):
            return True
    else:
        print(f"{symb} open price is 0")
        return False

    if(buyPrice > 0):  # ensure buyPrice has been initiated/is valid
        # if change since buy has gone beyond sell params
        if(inf['price']/buyPrice < sellDn(symb) or inf['price']/buyPrice >= sellUp(symb)):
            return True
        # if change since open has gone beyond sell params
        elif(inf['price']/inf['open'] < sellDn(symb) or inf['price']/inf['open'] >= sellUp(symb)):
            return True
        else:  # not enough change yet to consititute a sell
            return False
    else:
        return False

# get the sellUp value for a given symbol (default to the main value)


def sellUp(symb=""):
    lock = o.threading.Lock()
    lock.acquire()
    stockList = o.json.loads(open(c['file locations']['posList'], 'r').read())[
        'algos'][algo]
    lock.release()

    mainSellUp = float(c[algo]['sellUp'])  # account for squeeze here
    startSqueeze = float(c[algo]['startSqueeze'])
    squeezeTime = float(c[algo]['squeezeTime'])

    if(symb in stockList):
        # try setting the last jump, if it doesn't work, set it to yesterday TODO: this is logically wrong and should be fixed (something should change in the actual posList file)
        try:
            lastJump = o.dt.datetime.strptime(
                stockList[symb]['note'], "%Y-%m-%d").date()
        except Exception:
            lastJump = o.dt.date.today()-o.dt.timedelta(1)

        # after some weeks since the initial jump, the sell values should reach 1 after some more weeks
        # piecewise function: if less than time to start squeezing, remain constant, else start squeezing linearily per day
        sellUp = round(mainSellUp if(o.dt.date.today() < lastJump+o.dt.timedelta(startSqueeze*7)) else mainSellUp-(
            mainSellUp-1)*(o.dt.date.today()-(lastJump+o.dt.timedelta(startSqueeze*7))).days/(squeezeTime*7), 2)
    else:
        sellUp = mainSellUp
    return sellUp

# get the sellDn value for a given symbol (default to the main value)


def sellDn(symb=""):
    lock = o.threading.Lock()
    lock.acquire()
    stockList = o.json.loads(open(c['file locations']['posList'], 'r').read())[
        'algos'][algo]
    lock.release()

    mainSellDn = float(c[algo]['sellDn'])
    startSqueeze = float(c[algo]['startSqueeze'])
    squeezeTime = float(c[algo]['squeezeTime'])

    if(symb in stockList):
        try:  # try setting the last jump, if it doesn't work, set it to yesterday
            lastJump = o.dt.datetime.strptime(
                stockList[symb]['note'], "%Y-%m-%d").date()
        except Exception:
            lastJump = o.dt.date.today()-o.dt.timedelta(1)

        # after some weeks since the initial jump, the sell values should reach 1 after some more weeks
        # piecewise function: if less than time to start squeezing, remain constant, else start squeezing linearily per day
        sellDn = round(mainSellDn if(o.dt.date.today() < lastJump+o.dt.timedelta(startSqueeze*7)) else mainSellDn-(
            mainSellDn-1)*(o.dt.date.today()-(lastJump+o.dt.timedelta(startSqueeze*7))).days/(squeezeTime*7), 2)

    else:
        sellDn = mainSellDn
    return sellDn

# get the stop loss for a symbol (default to the main value)


def sellUpDn(symb=""):
    mainSellUpDn = float(c[algo]['sellUpDn'])
    # if there's ever any future enhancement that we want to add here, we can
    return mainSellUpDn
