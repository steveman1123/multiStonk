import _multistonks.otherfxns as o
import robin_account as apis
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
def getList(verbose=False):
    if(verbose):
        print(f"getting unsorted list for {algo}...")
    ul = getUnsortedList()
    if(verbose):
        print(f"found {len(ul)} stocks to sort through for {algo}.")
    if(verbose):
        print(f"finding stocks for {algo}...")
    # get dict of the list of stocks if they're good buys or not
    gb = goodBuys(ul)
    # print(f"found {gb} stocks for {algo}.")
    
    # the only time that the first char is a number is if it is a valid/good buy
    gb = {e: gb[e] for e in gb if gb[e][0].isnumeric()}
    # print(gb)
    if(verbose):
        print(f"{len(gb)} found for {algo}.")
    return gb



    
# determine if a list of stocks are good to buy or not
# returns a dict of {symb:validBuyText} where validBuyText should contain the failure reason or if it succeeds, then it is the initial jump date
def goodBuys(symbList, verbose=False):
    out = {}
    if(verbose):
        print(f"determining buys for {algo}: algorithm.\t {symbList}")
    prices = o.getPrices([e+"|stocks" for e in symbList])
    validStocks = [e.split("|")[0] for e in prices]  # only look at the valid stocks
    for ticker in validStocks:
        validBuy = str(o.dt.datetime.now().strftime("%Y-%m-%d"))

        out[ticker] = validBuy
        
    return out


# should return list of symbols
def getUnsortedList(verbose=False):
    symbList = list()
    symbList += apis.multistock_server(algo,c=None)
    if(verbose):
        print("Removing Duplicates...")
    symbList = list(dict.fromkeys(symbList))  # combine and remove duplicates

    return symbList



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
    prices = o.getPrices([s+"|stocks" for s in symbList])
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
def getUnsortedList(verbose=False):
    symbList = list()
    marketwatch, stocksunder = apis.multistock_server(algo,c)    
    symbList += marketwatch
    symbList += stocksunder    
    if(verbose):
        print("Removing Duplicates...")
    symbList = list(dict.fromkeys(symbList))  # combine and remove duplicates
    return symbList



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
