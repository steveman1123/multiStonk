#get all the trades made from a starting date and get relevent info into a csv file
#for analyzing win & loss rates

import alpacafxns as a
import json, csv
import datetime as dt

a.init("../stockStuff/apikeys/steve.txt",0)

#set up the range
startDate = "2021-04-20"
endDate = str(dt.date.today())

#get the trade data
print("\ngetting trade data")
trades = a.getTrades(startDate, endDate)[::-1]

print("formatting data")
#formatted as: symbol, date, side, price, qty, cumulative qty, avgBuyPrice (if buy, else blank), win/loss (if sell, else blank)

tradedSymbs = [] #make a list of the symbols only
out = [['symbol', 'date', 'side', 'price', 'qty', 'cumqty', 'avgBuyPrice', 'w/l']]
for t in trades:
  #get the transaction date
  try:
    xtnDate = str(dt.datetime.strptime(t['transaction_time'],"%Y-%m-%dT%H:%M:%S.%fZ").date())
  except ValueError:
    xtnDate = str(dt.datetime.strptime(t['transaction_time'],"%Y-%m-%dT%H:%M:%SZ").date())
  
  #get the numeric values of qty and price
  qty = int(t['qty'])
  price = float(t['price'])
  
  #if it's a buy, then set the params
  if(t['side']=='buy'):
    #if it hasn't been bought before
    if(t['symbol'] not in tradedSymbs):
      avgBuyPrice = price
      cumqty = qty

    #if it's already been bought before
    else:
      #get the latest instance of the symbol and the avgBuyPrice and cumulative qty for it
      latestAvgBuyPrice = out[len(out)-tradedSymbs[::-1].index(t['symbol'])-1][6]
      cumqty = out[len(out)-tradedSymbs[::-1].index(t['symbol'])-1][5]
      #calculate the new average buy price
      avgBuyPrice = (latestAvgBuyPrice*cumqty+price*qty)/(cumqty+qty)
      #add the new cumulative quantity
      cumqty += qty
      
    wl = ""
  
  #else if it's a sell, then set the params
  elif(t['side']=='sell'):
    #if it sells before buying, not enough info is known, so no data
    if(t['symbol'] not in tradedSymbs):
      avgBuyPrice = 0
      cumqty = 0
      wl = "NA"
    else:
      #get the latest instance of the symbol and the avgBuyPrice for it
      latestAvgBuyPrice = out[len(out)-tradedSymbs[::-1].index(t['symbol'])-1][6]
      cumqty = out[len(out)-tradedSymbs[::-1].index(t['symbol'])-1][5]
      #calculate whether it's a winning or losing trade
      wl = 'w' if price>latestAvgBuyPrice else 'l'
      #remove the new cumulative quantity
      cumqty -= qty
      avgBuyPrice = latestAvgBuyPrice
  
  #append the symbol to show it's been traded
  tradedSymbs += [t['symbol']]
  
  #append the data to the output
  out += [[t['symbol'],xtnDate,t['side'],price,t['qty'],cumqty,round(avgBuyPrice,4),wl]]

#for r in out:
#  print(*r,sep="\t")


#print("writing to file")
#writer = csv.writer(open("./tradeData.csv",'w+'),delimiter=',')
#writer.writerows(out)

print("calculating wins and loses\n")

#total wins and loses
tw = len([e for e in out if e[-1]=="w"])
tl = len([e for e in out if e[-1]=="l"])

avgwamt = [e[3]-e[6] for e in out if e[7]=="w"]
avgwamt = round(sum(avgwamt)/len(avgwamt),3)
avglamt = [e[3]-e[6] for e in out if e[7]=="l"]
avglamt = round(sum(avglamt)/len(avglamt),3)

print(f"total wins:\t{tw}")
print(f"total loses:\t{tl}")

print(f"avg win amt:\t{avgwamt}")
print(f"avg lose amt:\t{avglamt}")

print(f"win amt:\t{round(tw*avgwamt,3)}")
print(f"lose amt:\t{round(tl*avglamt,3)}")

print(f"Net earning:\t{round(tw*avgwamt-abs(tl*avglamt),3)}")