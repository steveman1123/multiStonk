# import alpacafxns as a
import json,sys
import datetime as dt
import ndaqfxns as n

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

configFile = "configs/multi.config"
pos = json.loads(open("alpaca-pos.json",'r').read())


c = n.configparser.ConfigParser()
c.read(configFile)
sys.path.append(c['file locations']['stockAlgosDir'])


#list of algorithms to be used and their corresponding stock lists to be bought (init with none)
algoList = c['allAlgos']['algoList'].replace(" ","").split(',') #var comes in as a string, remove spaces, and turn into comma separated list
algoList = {e:{} for e in algoList}

for algo in algoList: exec(f"import {algo}")

for algo in algoList:
  exec(f"{algo}.init('{configFile}')")

posList = json.loads(open("posListMulti.json",'r').read())['algos']


print(len(pos))
for algo in algoList:
  print(algo,len(posList[algo]))




verbose = True

for algo in posList:
    if(verbose): print(algo)
    #only the stocks in both posList[algo] and held positions
    #the stocks held by the given algo
    symbList = [e for e in pos if e['symbol'] in posList[algo]]
    
    #TODO: in each algo, add an error report if there's a stock that doesn't appear to be tradable (that is, it's in symbList but doesn't show up in getPrices)
    
    #get whether the stocks are good sells or not
    gs = eval(f"{algo}.goodSells(symbList,verbose=False)")
    
    print("posList",posList[algo])
    
    #go through the stocks of the algo
    for e in symbList:
      #only display/sell if not bought today
      if(posList[algo][e['symbol']]['lastTradeDate']<str(dt.date.today()) or posList[algo][e['symbol']]['lastTradeType']!='buy'):
        
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
        print("gs",gs)
        #mismatch between symblist (what's going into gs) and poslist (what's being displayed)
        if(gs[e['symbol']]==1): #if the stock is a good sell (sellUp)
          print("good to sell")

          # if(algo+"|"+e['symbol'] not in triggeredStocks): #make sure that it's not already present
          #   triggeredStocks.add(algo+"|"+e['symbol']) #if not, then add it to the triggered list
          # if("triggered" not in [t.name for t in n.threading.enumerate()]): #make sure that the triggered list isn't already running
          #   triggerThread = n.threading.Thread(target=checkTriggered) #init the thread - note locking is required here
          #   triggerThread.name = "triggered" #set the name to the algo and stock symb
          #   triggerThread.start() #start the thread

        elif(gs[e['symbol']]==-1): #else if it sells down (stop-loss)
          #sell immediately
          print(e['symbol'],"sell now")
          # sell(e['symbol'],algo)
  
  
