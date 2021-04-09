#this should be used to start generating a json file with the perceived sentiment of various headlines
import os, random, requests, time, json

filename = './analSent.json' #file to store the headlines and analysis

#make sure it's present, and init
if(os.path.isfile(filename)):
  sent = json.loads(open(filename,'r').read())
else:
  sent = {}

numHeads = 10 #arbitrary number of headlines to grab per stock (will save after this many headlines)
#get a list of symbols
stockList = json.loads(requests.get("https://raybb.github.io/random-stock-picker/stocks.json").text)


print("Use '+', '-', or any other key to indicate positive, negative or neutral sentiment respectively")

#loop forever
while True:
  symb = random.choice(stockList) #get a random stock from the list
  #get headlines for the stock
  r = json.loads(requests.get(f"https://api.nasdaq.com/api/news/topic/articlebysymbol?q={symb}%7Cstocks&offset=0&limit={numHeads}",headers={'user-agent':'-'},timeout=5).text)
  
  #loop through each headline
  for e in r['data']:
    vote = input(e['title']+"\n") #get the user input
    if(e['title'] not in sent): #init if headline not present already
      sent[e['title']] = {'votes':0,'sent':0}
    #populate with inputted data (incriment vote count and change sentiment value)
    sent[e['title']]['votes'] += 1
    if('+' in vote):
      sent[e['title']]['sent'] += 1
    elif('-' in vote):
      sent[e['title']]['sent'] -= 1
    
  print("Saving...")
  open(filename,'w').write(json.dumps(sent))
    
    
    