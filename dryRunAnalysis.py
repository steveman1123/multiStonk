import json,sys
import matplotlib.pyplot as plt
import datetime as dt
import otherfxns as o


algo = 'earn'
listDir = "../stockStuff/dryRunLists/"

j = json.loads(open(listDir+algo+'.json','r').read())

l = [[e,j[e]['low'],j[e]['lowDate'],j[e]['high'],j[e]['highDate'],j[e]['purchDate']] for e in j] #convert the json data to a list (symb, data)

l.sort(key = lambda x: x[1]) #sort list by second element




print("\n\n\n")
tgt1 = 0.92
tgt2 = 1.25

low = [s[0] for s in l if s[1]<tgt1]
med = [s[0] for s in l if s[1]>=tgt1 and s[3]<=tgt2]
high = [s[0] for s in l if s[3]>tgt2]

print(f"less than {tgt1}:\t\t{len(low)}")
print(f"btw {tgt1} & {tgt2}:\t{len(med)}")
print(f"greater than {tgt2}:\t{len(high)}")
print(len(low)+len(med)+len(high))
print(len(l))

#print("symb\tbuyDate\t\tbuyPrice\thigh\thiDate\t\tlo\tloDate\t\tnote")
#print("----\t-------\t\t--------\t----\t------\t\t--\t------\t\t----")
'''
for e in l:
  #print(f"{e}\t{j[e]['purchDate']}\t{j[e]['buyPrice']}\t\t{j[e]['high']}\t{j[e]['highDate']}\t{j[e]['low']}\t{j[e]['lowDate']}\t{j[e]['note']}")

  #earnings surprise
  surp = json.loads(o.requests.get(f"https://api.nasdaq.com/api/company/{e[0]}/earnings-surprise",headers={"user-agent":"-"},timeout=5).text)
  fcast = json.loads(o.requests.get(f"https://api.nasdaq.com/api/analyst/{e[0]}/earnings-forecast",headers={"user-agent":"-"},timeout=5).text)
  eps = json.loads(o.requests.get(f"https://api.nasdaq.com/api/quote/{e[0]}/eps",headers={"user-agent":"-"},timeout=5).text)
  
  surpout=None
  if(surp['data'] is not None and surp['data']['earningsSurpriseTable'] is not None):
    surp = surp['data']['earningsSurpriseTable']['rows']
    surpout = [e[0]+" surp"]+[s['dateReported']+"\t| "+s['percentageSurprise'] for s in surp]
  
  fcastout=None
  if(fcast['data'] is not None and fcast['data']['quarterlyForecast'] is not None):
    fcast = fcast['data']['quarterlyForecast']['rows']
    fcastout = [e[0]+" fcast"]+[f"{s['fiscalEnd']}\t| {s['lowEPSForecast']}-{s['highEPSForecast']}" for s in fcast]
  
  epsout=None
  if(eps['data'] is not None and eps['data']['earningsPerShare'] is not None):
    eps = eps['data']['earningsPerShare']
    epsout = [e[0]+" eps"]+[f"{s['period']}\t| {s['consensus']}\t| {s['earnings']}" for s in eps]
  
  if(surpout is not None and fcastout is not None and epsout is not None):
    print(*e,sep="\t")
    print(*surpout,sep="\n")
    print(*fcastout,sep="\n")
    print(*epsout,sep="\n")
    print("\n")

'''

'''
# *** plot stuff ***
stocks = [e[0] for e in l] #isolate the symbols
lookBackDays = 30

for s in stocks:
  #print(s)
  #hist = o.getHistory(s,j[s]['purchDate'],str(dt.date.today())) #get history
  hist = o.getHistory(s,str(dt.datetime.strptime(j[s]['purchDate'],"%Y-%m-%d").date()-dt.timedelta(lookBackDays)),str(dt.date.today())) #get history
  #hist = o.getHistory(s) #get history
  dates = [dt.datetime.strptime(e[0],"%m/%d/%Y") for e in hist] #convert dates to dt format
  prices = [float(e[1]) for e in hist] #isolate the closing prices
  normPrices = [p/prices[-1] for p in prices] #normalize prices based on the first value
  #plt.plot(dates,normPrices,label=s) #plot the line
  normPrices.reverse() #use when not using dates
  plt.plot(normPrices,label=s) #plot the line

#plt.xlabel('date')
plt.xlabel(f'days since bought (minus {lookBackDays})')
plt.ylabel('price (normalized)')
plt.legend(bbox_to_anchor=(1,1), loc="upper left")
plt.show()

# *** end plotting ***
'''