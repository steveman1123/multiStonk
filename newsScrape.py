#the goal of this file is to scrape various financial news sites with regards to individual stocks

'''
sites to look at:
yahoo finance - works, very large site
nasdaq - works, slightly large site (might not actually work, looks js driven)
marketwatch - works, very large site
reuters - doesn't quite work
seekingalpha - requires js
cnbc - works, very large site

'''

import alpacafxns as a

def scrapeYF(symb):
  # print("Getting yahoo finance news...")
  while True:
    try:
      r = a.o.requests.get(f"https://finance.yahoo.com/quote/{symb}",headers={"user-agent":"-"},timeout=5).text #get data
      s = a.o.bs(r,'html.parser') #make it soup
      break
    except Exception:
      print("Connection Error...")
      a.o.time.sleep(3)
      continue

  #TODO: see if a date is available, if so, add it, if not, make a note of it
  txt = [d.findAll(text=True) for d in s.select("#quoteNewsStream-0-Stream")[0].findAll('div')] #narrow down to news articles
  txt = [[e for e in t if ("react" not in e)] for t in txt if len(t)>1] #remove titles, blanks, and random react text
  newTxt = []
  for t in txt:
    if t not in newTxt: #remove duplicates
      newTxt.append(t)
  
  out = []
  for i,t in enumerate(newTxt): #convert from list of lists to list of dicts
    for j,e in enumerate(t):
      if(j==0):
        out.append({'source':e})
      if(j==1):
        out[i]['title'] = e
      if(j==2):
        out[i]['abstract'] = e
    out[i]['date'] = ""

  return out


#get new from the nasdaq api. this currently probably only works with stocks, and not any other security
def scrapeNASDAQ(symb,headNum=5):
  while True:
    try:
      #the following two return essentially the same information, however quote-news returns slightly more than recent-articles
      r = json.loads(requests.get(f"https://www.nasdaq.com/api/v1/quote-news/{nasNewsNum(symb)}/{headNum}",headers={"user-agent":'-'}, timeout=5).text)
      # r = json.loads(requests.get(f"https://www.nasdaq.com/api/v1/recent-articles/{symbNewsNum(symb)}/{headNum}",headers={"user-agent":'-'}, timeout=5).text)
      break
    except Exception:
      print(f"Error in getNews for {symb}. Trying again...")
      time.sleep(3)
      pass
  return r

  
#get the number used in the quote-news and recent-articles nasdaq api's
#NOTE: this is a totally sketch way to get this and we really should figure out how to translate the number because it can look at more than just stocks
def nasNewsNum(symb, maxTries=3):
  tries = 0
  num=0
  while tries<maxTries:
    try:
      r = requests.get(f"https://www.nasdaq.com/market-activity/stocks/{symb}",headers={"user-agent":'-'}, timeout=5).text
      num = int(r.split('data-symbol-id="')[1].split('">')[0])
      break
    except Exception:
      print(f"Error in symbNewsNum for {symb} ({tries+1}/{maxTries}. Trying again...")
      time.sleep(3)
      tries += 1
      pass
  return num


#TODO: check out the html from this site to see their quote api (in js near the top of the page)
def scrapeCNBC(symb):
  # print("Getting cnbc news...")
  while True:
    try:
      r = a.o.requests.get(f"https://www.cnbc.com/quotes/?symbol={symb}",headers={"user-agent":"-"},timeout=5).text
      break
    except Exception:
      print("Connection Error...")
      a.o.time.sleep(3)
      continue

  #data is stored in js var symbolInfo
  inf = r.split('symbolInfo = ')[1].split(';\n')[0] #isolate symbol info
  inf = a.o.json.loads(inf) #convert to json
  try:
    inf = inf['assets']['partner']['rss']['channel']['item'] #isolate news
  except Exception:
    inf = []

  #remove extra data and rename needed ones
  for e in inf:
    try:
      e.pop("metadata:credit",None)
      e.pop("metadata:image",None)
      e.pop("metadata:company",None)
      e.pop("metadata:contentType",None)
      e.pop("metadata:id",None)
      e.pop("metadata:entitlement",None)
      e.pop("metadata:tickersymbol",None)
      e.pop("link",None)
      e.pop("guid",None)
      e.pop("category",None)

      e['abstract'] = e.pop("description",None)
      e['source'] = e.pop('metadata:source',None)
      e['date'] = e.pop('pubDate',None)
    except Exception:
      continue

  return inf


#market watch
#press releases require js, but news does not. Figure out source and get both
def scrapeMW(symb):
  # print("Getting market watch news...")
  r = a.o.requests.get(f"https://www.marketwatch.com/investing/stock/{symb}", headers={"user-agent":"-"},timeout=5).content
  #s = a.o.bs(r,'html.parser')
  print(r)


#combine all different news sources
def scrape(symb):
  # print(f"Getting {symb} news")
  try: #sometimes YF or CNBC returns a dict (somehow?), so the final output throws an error because it can't be concatinated
    out = scrapeYF(symb)+scrapeCNBC(symb)#+scrapeNASDAQ(symb) #TODO: ensure all are in the correct format
  except Exception:
    try:
      out = scrapeCNBC(symb)
    except Exception:
      out = []
  return out

