#this file contains functions specifically for the meme stocks algo
#how do stocks move after being discussed on reddit, other unofficial forums like 4chan (in wallstreetbets, etc)?

# https://www.reddit.com/dev/api
# https://github.com/reddit-archive/reddit/wiki/API
# https://api.reddit.com/search?q={symb}+subreddit%3A{sub}+nsfw%3Ano+self%3Ayes&sort=relevance&t=month
# https://www.reddit.com/r/wallstreetbets/new/

#TODO: use this api for reddit sent analysis: https://api.pushshift.io/reddit/search/comment/?subreddit=
# ^ https://github.com/pushshift/api

import otherfxns as o

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

#get list of stocks pending FDA approvals
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"finding stocks for {algo}...")
  arr = goodBuys(ul) #returns dict of {symb:gooduy(t/f)}
  arr = {e:"-" for e in arr if(arr[e])} #only look at the ones that are true
  if(verbose): print(f"{len(arr)} found for {algo}.")
  
  return arr

#get a list of stocks to be sifted through
#return dict of format {symb:{sub:score}} where the score is the sub weight*how many mentions the symb has
def getUnsortedList(verbose=False):
  subs = {'wallstreetbets':1,'stocks':1,'pennystocks':0.95,'superstonk':0.9,'stockmarket':0.95}
  out = {}
  for sub in subs:
    while True:
      try:
        r = o.requests("reddit API for various market subs",timeout=5)
        break
      except Exception:
        print("Error getting unsorted list for reddit algo. Trying again...")
        o.time.sleep(3)
        pass
  
  return []


#return a dict of if they're a good buy or not {symb:t/f}
def goodBuys(symbList,verbose=False):
  
  return gb

#return a dict of {symb:t/f} for if they're good to sell or not
def goodSells(symbList,verbose=False):
  print("algo incomplete")
  
  if(verbose): print(f"stocks in prices: {list(prices)}")
  #check that it has exceeded the stopLoss or takeProfit points
  gs = {}
  for s in symbList:
    if(s in prices):
      if(verbose): print(f"{s}\topen: {round(prices[s]['price']/prices[s]['open'],2)}\tbuy: {round(prices[s]['price']/buyPrices[s],2)}\tsellUp: {sellUp(s)}\tsellDn: {sellDn(s)}")
      #check if price triggered up
      if(prices[s]['price']/prices[s]['open']>=sellUp(s) or prices[s]['price']/buyPrices[s]>=sellUp(s)):
        gs[s] = 1
      #check if price triggered down
      elif(prices[s]['price']/prices[s]['open']<sellDn(s) or prices[s]['price']/buyPrices[s]<sellDn(s)):
        gs[s] = -1
      else: #price didn't trigger either side
        gs[s] = 0
    else:
      gs[s] = 0
  
  return gs


#TODO: this should also account for squeezing
def sellUp(symb=""):
  mainSellUp = float(o.c[algo]['sellUp'])
  if(symb in stockList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  mainSellDn = float(o.c[algo]['sellDn'])
  if(symb in stockList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(o.c[algo]['sellUpDn'])
