#get stocks poised for fda approval

'''
based on collected data:
target gain of +30%
if it doesn't gain in the first 2 weeks, it probably won't gain much later


'''
print("Initializing algo 2...")
import configparser, json, time

cfg = configparser.ConfigParser()

cfg.read('./algo2.config') #file containing paths to other files, and other settings including bPow margin, target amounts, dates, etc 

commonConfigFile = cfg['File Locations']['common config file'] #file containing settings that will be shared across algorithms such as master/slave addresses, api key location, common
infFile = cfg['File Locations']['info file'] #file containing info about the account/algo such as buying power, portfolio value, status (errored or not), max port value to hold (based on some % of the total market cap of the held stocks), and anything else we feel should be included (tbd)
histFile = cfg['File Locations']['history file'] #file containing stock trade histories including trade dates, types, amounts (prices, shares)


#get common config data
#this one does not check for if it's missing because if it's not, there's big problems and we don't want to run anyways
with open(commonConfigFile,'r') as f:
  cc = json.loads(f.read())


#get history data
#ensure that the file exists, if it doesn't, populate with default values and create/recreate the file
try:
  with open(histFile,'r') as f:
    hist = json.loads(f.read())
except Exception:
  print("Error: info file does not exist or contains invalid data. Loading defaults")
  #create file and populate with default values
  #TODO: should be given any unclaimed stocks (the main program should be able to see which algos have what, and whatever isn't claimed can go into this one)
  hist = {symb:{timestamp:{'side':side,'sharePrice':sharePrice,'numShares':numShares}} #generate default values here 
  with open(histFile,'w') as f:
    f.write(json.dumps(hist))

#get info data
try:
  with open(infFile,'r') as f:
    inf = json.loads(f.read())
except Exception:
  print("Error: info file does not exist or contains invalid data. Loading defaults")
  #create file and populate with default values
  #TODO: should be given any unclaimed cash based (amounts given from the main program, like in hist), portfolio value can then be cash+held stocks found in hist
  inf = {'cash':cash,'portVal':cash+sum(hist),'maxPortVal':mktCapPerc*sum(hist[symb][mktCap]),'status':'ok'}
  with open(infFile,'w') as f:
    f.write(json.dumps(inf,indent=2))



#load custom modules and paths

sys.path.insert(0,'../common')
import algo2fxns as a2
import alpacafxns as a
import otherfxns as o

print("Algo 2 ready.")


#TODO: everything past this line needs to be rewritten to account for the changes above and to include real trading

#the idea here is to get a list of penny stocks in healthcare and look at fda news regarding new drug releases
maxPrice = cfg['Buy Params']['maxPrice']


'''
-at the end of every day, get stocks from the drug lsit
-narrow down to the right price
-ensure they're not doing reverse stock split or going bankrupt
-buy int(cash/numStocks) $ worth of each stock

for held stocks:
if timeSinceBuy<timeToHold:
  if price>sellUp*buyPrice:
    sell
  elif price<sellDn*buyPrice:
    sell
  else:
    hold
else:
  sell

check every hour
'''

while True:
  if(a.marketIsOpen()):
    #for held stocks
    for e in a2.getPos(infFile):
      hist = a2.getHist(e,histFile)
      if(dt.datetime.today().date()-dt.datetime.strpt(initialTradeDate(hist),'date format')>cfg['Time Params']['maxTime']):
        print("Too long ago")
        sell
      elif(o.getPrice(e))
      
    
    time.sleep(3600)
  else:
    stockList = o.getDrugList()
    stockList = [e for e in stockList if o.getPrice(e)<=maxPrice]
    time.sleep(a.timeTillOpen())
    
    