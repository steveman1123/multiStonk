#get stocks poised for fda approval

'''
based on the alpacaalgos script - the original good bot

'''
print("Initializing algo1...")
import configparser, json

cfg = configparser.ConfigParser()

cfg.read('./algo1.config') #file containing paths to other files, and other settings including bPow margin, target amounts, dates, etc 

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

import alpacafxns as a
import algo1fxns as a1
import otherfxns as o

print("Algo1 ready.")

