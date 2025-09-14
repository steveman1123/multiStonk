#this file contains functions that all algo files should have and their return formats

import ndaqfxns as n
import os,json,threading,time,configparser
import datetime as dt
from otherfxns import *

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

#initiate the algo with the path to the config file
def init(configFile):
  global posList,c
  #set the multi config file
  #TODO: add error if the file doesn't exist.
  #TODO: in otherfxns, from configparser import ConfigParser (since I don't think we use anthing else)
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()


#get a list of potential gainers according to this algo
def getList(verbose=True):
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList()
  if(verbose): print(f"found {len(ul)} stocks to sort through for {algo}.")
  if(verbose): print(f"finding stocks for {algo}...")
  gb = goodBuys(ul) #get dict of the list of stocks if they're good buys or not
  if(verbose): print(f"{len(gb)} found for {algo}.")
  return gb


#determine if a list of stocks are good to buy or not
#returns a dict of {symb:validBuyText} where validBuyText should contain the failure reason or if it succeeds, then it is the initial jump date
def goodBuys(symbList, days2look=-1, verbose=False):
    
  return out

#perform the same checks as goodSell but multiplexed for fewer requests
#return dict of {symb:goodSell (-1=sellDn, 0=hold, 1=sellUp)}
#TODO: thi should probably be adjusted?
def goodSells(symbList, verbose=False): #symbList is a list of stocks ready to be sold
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo] #load up the stock data for the algo
  lock.release()
  symbList = [e for e in symbList if e in posList] #only look at the stocks that are in the algo
  buyPrices = {s:float(posList[s]['buyPrice']) for s in symbList} #get buyPrices {symb:buyPrce}
  prices = o.getPrices([s+"|stocks" for s in symbList]) #currently format of {symb|assetclass:{price,vol,open}}
  prices = {s.split("|")[0]:prices[s] for s in prices} #now format of {symb:{price,vol,open}}
  
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

  #display stocks that have an error
  for e in [e for e in symbList if e not in gs]:
    print(f"{e} not tradable")
  
  return gs


#get list of stocks from stocksUnder1 and marketWatch lists
#should return list of symbols
def getUnsortedList(verbose=False, maxTries=3):
    
  if(verbose): print("Removing Duplicates...")
  symbList = list(dict.fromkeys(symbList)) #combine and remove duplicates

  return symbList


#get the sellUp value for a given symbol (default to the main value)
def sellUp(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  mainSellUp = float(c[algo]['sellUp']) #primary sellUp value
  
  if(symb in posList):
    sellUp = mainSellUp #account for change sellUp value here based on date or other params here
  else:
    sellUp = mainSellUp
  return sellUp


#get the sellDn value for a given symbol (default to the main value)
def sellDn(symb=""):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  mainSellDn = float(c[algo]['sellDn']) #primary sellDn value
  
  if(symb in posList):
    sellDn = mainSellDn #account for change sellDn value here based on date or other params here
  else:
    sellDn = mainSellDn
  return sellDn

#get the stop loss for a symbol (default to the main value)
def sellUpDn(symb=""):
  mainSellUpDn = float(c[algo]['sellUpDn'])
  #if there's ever any future enhancement that we want to add here, we can
  return mainSellUpDn
