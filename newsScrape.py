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

import time, json, requests, re
from bs4 import BeautifulSoup as bs

def scrapeYF(symb, maxTries=3):
  # print("Getting yahoo finance news...")
  tries=0
  while tries<maxTries:
    try:
      r = requests.get(f"https://finance.yahoo.com/quote/{symb}",headers={"user-agent":"-"},timeout=5).text #get data
      s = bs(r,'html.parser') #make it soup
      break
    except Exception:
      print("No connection or other error encountered in scrapeYF. Trying again...")
      tries+=1
      time.sleep(3)
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
def scrapeNASDAQ(symb,headNum=5,maxTries=3):
  tries=0
  while tries<maxTries:
    try:
      r = json.loads(requests.get(f"https://api.nasdaq.com/api/news/topic/articlebysymbol?q={symb}%7Cstocks%26limit={headNum}",headers={"user-agent":'-'}, timeout=5).text)
      break
    except Exception:
      print(f"Error in getNews for {symb}. Trying again...")
      tries+=1
      time.sleep(3)
      pass
  return r


#get news from duckduckgo
def scrapeDDG(symb, maxTries=3):
  out={}
  tries=0
  while tries<maxTries:
    try:
      #TODO: vqd should be changed or figure out what it means
      #original vqd=3-27594420679728440418432461322182106813-319083102909836812520935867132683714843
      out = o.json.loads(requests.get(f"https://duckduckgo.com/news.js?o=json&q={symb}&vqd=3-27594420679728440418432461322182106813",headers=o.HEADERS,timeout=5).text)
      break
    except Exception:
      print(f"No connection or other error encountered in scrapeDDG for {symb}. Trying again...")
      tries+=1
      time.sleep(3)
      continue
  
  return out




#TODO: check out the html from this site to see their quote api (in js near the top of the page)
def scrapeCNBC(symb):
  # print("Getting cnbc news...")
  while True:
    try:
      r = requests.get(f"https://www.cnbc.com/quotes/?symbol={symb}",headers={"user-agent":"-"},timeout=5).text
      break
    except Exception:
      print("Connection Error...")
      time.sleep(3)
      continue

  #data is stored in js var symbolInfo
  inf = r.split('symbolInfo = ')[1].split(';\n')[0] #isolate symbol info
  inf = json.loads(inf) #convert to json
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
  r = requests.get(f"https://www.marketwatch.com/investing/stock/{symb}", headers={"user-agent":"-"},timeout=5).content
  s = bs(r,'html.parser')
  
  print(r)


#analyze the sentiment of a given string to return if it has a positive or negative tone
def analSent(text):
  sentFile = '../stockStuff/wordScores.json' #file containing the weight of every word
  # sentiment calc is something like sum(averages sents of each word)/number of words
  # TODO: there should also be a confidence number as well (calculated based on number of votes)
  # confidence should be calculated according to the number of votes (more votes=more confidence (and similar number of votes per word))
  # confidence could be min^2/max number of votes? That way we get relative spread of votes  with basis on the minimum?
  # or could be avgVotes*min/max
  
  # get the word sentiments
  wordScores = json.loads(open(sentFile,'r').read())
  
  # clean string to only have lowercase letters and spaces then split by spaces
  text = re.sub("/[^A-Za-z ]/","",text).split(" ")
  
  sent = 0
  conf = 0
  for w in text:
    if(w in wordScores):
      sent += wordScores[w]['sent']/wordScores[w]['votes']
      conf += wordScores[w]['votes']

  sent /= len(text) #average sentiment over number of words
  conf /= len(text) #average votes over number of words
  return {"sent":sent,"conf":conf}
  

#search a list of subreddits for a given symb
#suggested subreddits: wallstreetbets, pennystocks, stocks,
# more info: https://www.reddit.com/dev/api#GET_search
#TODO: figure out how to only return text posts (no images or videos)
def scrapeReddit(symb, subList, maxTries=3):
  subList = list(set(subList)) #remove duplicates
  r = {} #init output
  for sub in subList: #for every subreddit in the list
    tries=0
    while tries<maxTries:
      try:
        r[sub] = json.loads(requests.get(f"https://api.reddit.com/search?q={symb}+subreddit%3A{sub}+nsfw%3Ano+self%3Ayes&sort=relevance&t=month",headers={"user-agent":"-"},timeout=5).text) #restrict to selected subreddit, no nsfw, include text posts, relevance over the past month
        break
      except Exception:
        print(f"No connection or other error encountered in scrapeReddit for {symb} in {sub}. Trying again...")
        tries+=1
    return r
    


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

