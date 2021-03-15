#use this file to test a single algo out of the algos folder
#meant for a single alpaca acct

import alpacafxns as a
import otherfxns as o
import threading,json,time,sys
import datetime as dt

algo = 'ema'

exec(f"import {algo}")

posListFile = o.c['file locations']['posList']
stocks2buy = []

def main():
  global posList,posListFile,stocks2buy
  while True:
    if(a.marketIsOpen()):
      print("Market is open")
      #update stock list if need be
      try:
        posList = json.loads(open(posListFile,'r').read())
      except Exception: #if it fails, populate it with the most recent data
        print("Error reading posList file. Populating...")
        posList = {}
        for p in a.getPos():
          trades = a.getStockTrades(symb)
          posList[p] = {
                        'tradeDate':trades[0]['transaction_time'][:10] if len(trades)>0 else 'NA',
                        'tradeType':trades[0]['side'] if len(trades)>0 else 'NA',
                        'shouldSell':False
                        }
    
        open(posListFile,'w').write(json.dumps(posList))
      
      if(len(stocks2buy)==0):
        updateThread = threading.Thread(target=updateList(),args=o.reverseSplitters())
        updateThread.setName("update")
        updateThread.start()
    
      acct = a.getAcct()
      print(f"Portfolio value: ${acct['portfolio_value']}, cash: ${acct['cash']}")
    
      check2sell()
      if(a.timeTillClose()<10*60):
        check2buy()
      time.sleep(60)
    else:
      print("Market closed.")
      tto = a.timeTillOpen()
      print(f"Market opens in {round(tto/3600,2)} hours")
      #wait some time before the market opens      
      if(tto>60*float(o.c['time params']['updateLists'])):
        print(f"Updating stock lists in {round((tto-60*float(o.c['time params']['updateLists']))/3600,2)} hours")
        time.sleep(tto-60*float(o.c['time params']['updateLists']))
      #update stock lists
      stocks2buy = eval(f"{algo}.getList()")
    
      time.sleep(a.timeTillOpen())
    
  

def check2sell():
  global posList
  print("symb\tcng frm buy\tcng frm cls\tsell lims")
  print("----\t-----------\t-----------\t---------")
  for p in a.getPos():
    sellUp = float(eval(f"{algo}.sellUp({p['symbol']})"))
    sellDn = float(eval(f"{algo}.sellDn({p['symbol']})"))
    buyPrice = float(p['avg_entry_price'])
    curPrice = float(p['current_price'])
    print(f"{symb}\t{round(curPrice/buyPrice,2)}\t\t{round(1+float(p['change_today']),2)}\t\t{round(sellDn,2)} & {round(sellUp,2)}")
    if(posList[p]['tradeDate']!=str(dt.date.today()) or posList[p]['tradeType']!='buy'):
      if(curPrice/buyPrice >= o.c[algo]['sellUp'] or curPrice/buyPrice < o.c[algo]['sellDn'] or posList[p]['shouldSell']):
        r = a.createOrder("sell",p['qty'],p['symbol'])
        if(r.endswith("accepted")):
          posList[p]['tradeDate'] = str(dt.date.today())
          posList[p]['tradeType'] = 'sell'
          open(posListFile,'w').write(json.dumps(posList))
        

def check2buy(stocks2buy):
  global posList
  cash = float(a.getAcct()['cash'])
  cashPerStock = max(cash/len(stocks2buy),float(o.c['account params']['minDolPerStock']))
  if(len(stocks2buy)>0):
    while cash>cashPerStock:
      random.shuffle(stocks2buy) #shuffle the lsit so its different every time
      cashPerStock = max(cash/len(stocks2buy),float(o.c['account params']['minDolPerStock'])) #dollars to throw at a single stock
      numStocks = int(len(stocks2buy)/cashPerStock) #total number of stocks to buy this round
      for s in stocks2buy[:min(numStocks,len(stocks2buy)-1)]:
        curPrice = a.getPrice(s)
        r = createOrder('buy',int(curPrice/cashPerStock),s)
        if(r.endswith('accepted')): #make sure that it actually worked
          posList[s] = { #update the record
                        'tradeDate':str(dt.date.today()),
                        'tradeType':'buy',
                        'shouldSell':False
                        }
          open(posListFile,'w').write(json.dumps(posList))
      cash = float(a.getAcct()['cash'])
  else:
    print("No stocks to buy")
  
  
def updateList(rm=[]):
  print(f"Updating {algo} stock list")
  global stocks2buy
  algoBuys = eval(f"{algo}.getList()")
  algoBuys = [e for e in algoBuys if e not in rm] #remove any stocks that are in the rm list
  stocks2buy = algoBuys
  print("Done updating list")
  

if(__name__ == '__main__'):
  main()

