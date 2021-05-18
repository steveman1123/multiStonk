#this file contains functions specifically for the earnings
#what happens to a stock after various earnings calls?

# https://tradingreviews.net/why-stock-prices-fall-after-good-earnings-announcements
# https://www.marketwatch.com/story/heres-how-to-trade-a-stock-after-an-earnings-surprise-2016-08-18
# https://finance.zacks.com/impact-earnings-announcements-stock-prices-4265.html
# https://www.investopedia.com/terms/e/earningssurprise.asp


import otherfxns as o
# import newsScrape as ns

algo = o.os.path.basename(__file__).split('.')[0] #name of the algo based on the file name

def init(configFile, verbose=False):
  global posList,c
  #set the multi config file
  c = o.configparser.ConfigParser()
  c.read(configFile)
  
  #stocks held by this algo according to the records
  lock = o.threading.Lock()

  #TODO: do these checks for all algos
  if(o.os.path.isfile(c['file locations']['posList'])):
    lock.acquire()
    posList = o.json.loads(open(c['file locations']['posList'],'r').read())
    lock.release()
    if(algo in posList):
      posList = posList[algo]
    else:
      if(verbose): print(f"{algo} not found the posList")
      posList = {}
  else:
    if(verbose): print("posList file does not exist")
    posList = {}
    


'''
https://seekingalpha.com/article/1445911-a-remarkably-reliable-way-to-predict-post-earnings-price-moves
1. Stock price action in the most recent weeks.
If stock moved steadily higher for month leading to announcement, particularly for last week, expectations might be escalating. Conversely, if stock moved lower leading to the announcement, expectations might be low and stock might move higher even if the company merely matches analyst estimates.

2. Whisper numbers vs. analyst estimates.
If whisper numbers are significantly higher than analyst estimates, expectations are high. There is a challenge here to check out whisper numbers from a reliable source (there is wide range of reliability from various sources).

3. Recent post-earnings price changes compared to earnings results (is there a pattern for that company)?
Some companies display remarkably consistent patterns of meeting or beating estimates, and subsequent stock price changes. For example, JPM beat estimates handily for four consecutive quarters but the stock fell half the time after they reported results, and CRM crushed estimates every time and the stock rose every time (by an average of 6.6%). Some of these patterns can be counted on to persist.
Another pattern has been companies whose stock price didn't fluctuate very much regardless of whether they met, fell short of, or exceeded estimates. These companies seem perfectly suited for calendar spread strategies or buy-write strategies (benefiting from the escalated implied volatility of the weekly options).

4. Current RSI levels.
If a company in "very overbought" condition leading up to announcement, it might be an indication of extremely high expectations, although overbought readings have not been as reliable as oversold conditions that demonstrate that expectations are unusually low.

5. Overwhelming positive (or negative) comments on various blog posts.

I always check out recent articles on the company published by Seeking Alpha and especially the comments at the end of the articles, as well as blog posts on other financial forums. For the most part, I consider this commentary as contrary indicators. The people who seem to be the most impassioned about loving or hating a company also seem to be wrong most of the time.

In addition, I check out recent hedge fund activity (are hedge funds buying or selling the stock?) to get a better handle on whether the stock is likely to rise or fall after the announcement. While hedge funds are not always right, they can be counted on to have conducted some serious due-diligence work before making a decision to commit or divest, and they have far more resources at their disposals than any individual could hope to have. It seems to be a good idea to piggy-back on their work, and to join them in their assessment of the company.

I have found that actual hedge fund cash commitments is a much better indicator of future stock performance than anything the analysts say. For example, for the last four quarters, analysts who publish estimates for SalesForce.com (NYSE:CRM) have been off by an average of ten times earnings per share for the past four quarters (e.g., they estimated an average of $.03 and actual earnings were over $.30). It is hard to give the analysts any credence when they can consistently be this far off base.

One shortcoming of the model is that it doesn't always provide predictive value. In one article I reviewed the expectation levels for eight reporting companies and concluded that none of them displayed unusually high or low expectation levels so that my model could not help in predicting the post-earnings stock price move -- Predicting The Direction Of Next Week's Earnings-Reporting Companies
'''

#return dict of good buys of format {symb:note}
#where the note contains the earnings date
def getList(verbose=True):
  #perform checks to see which one ones will gain
  maxPrice = float(c[algo]['maxPrice']) #max price point
  minPrice = float(c[algo]['minPrice']) #min price point
  
  #each check will add or subtract from a score  (as lacking one or more of the indicators isn't necessarily a dealbreaker)
  ul = getUnsortedList() #format of {date, inf:{lastYrRpt,lastYrEPS,time,symb,name,mktcap,fiscQuartEnd,epsFrcst,numEsts}}
  earnDate = ul['date'] #get the date before it's stripped off
  prices = o.getPrices([e['symbol']+"|stocks" for e in ul['inf']])
  prices = {s.split("|")[0]:prices[s]['price'] for s in prices} #isolate to {symb:price}
  ul = [e for e in ul['inf'] if(e['symbol'] in prices and minPrice<=prices[e['symbol']]<=maxPrice)] #only keep elements that are in prices and within our price range

  if(verbose): print(f"{len(ul)} potential earners on {earnDate}")
  
  goodBuys = {e['symbol']:earnDate for e in ul} #during normal running, this should be empty dict
  '''
  for i,e in enumerate(ul):
    if(verbose): print(f"\n({i}/{len(ul)})\t{e['symbol']}")
    hist = o.getHistory(e['symbol'],startDate=str(o.dt.date(o.dt.date.today().year-1,(o.dt.date.today().month-3-1)%12+1,o.dt.date.today().day))) #get the last year and 3 months worth of history
    if(verbose): print(f"{len(hist)} days available")
    #check that the price has been going up or down or steady over the past few weeks (high, low, or neutral expectations)
    #compare whisper numbers to predicted? (significantly higher/lower should indicate high/low expectations)
    #skip for now. Must find good sources of whisper numbers
    #compare price changes to previous earning price changes (does it consistantly go up/dn after a hit/miss?)
    earnDates = o.getEarnInf(e['symbol']) #get previous earning call dates
    #overbought >> rsi>=0.7, oversold >> rsi<=0.3
    rsi = getRSI(hist)
    #check blog/reddit/other news sentiments
    holdings = o.getInstAct(e['symbol']) #check hedge funds activity regarding it
        
    score = 0 #init the goodBuy score
    smac6 = o.mean([float(e[1]) for e in hist[5*6:5*7]]) #get the current sma from 6 weeks ago
    smac2 = o.mean([float(e[1]) for e in hist[5*2:5*3]]) #get the current sma from 2 weeks ago
    cpurch = float(hist[0][1]) #not the actual nominal purchase price, but the most recent closing price (yesterday, as nominally this should be run pre-premarket)
    tol62 = float(c[algo]['tol62']) #tolerance for the 6 week to 2 week comparison
    tol6p = float(c[algo]['tol6p']) #tolerance for the 6 week to purchase price comparison
    tol2p = float(c[algo]['tol2p']) #tolerance for the 2 week to purchase price comparison
    #see how previous earning price changes happen (if there's a pattern that could occur)
    for d in earnDates:
      #looking for consistancy:
      #see how price is affected if eps is reached or not (if it consistantly goes up or down, or it doesn't)
      #check SMA at 6wks before
      #TODO: adjust how this get factored into the scoring (and max scoring)
      if(d in [e[0] for e in hist]): #ensure that the date can be found (sometimes there isn't enough data to actually see it)
        didx = [e[0] for e in hist].index(d) #date index in hist
        #check 2 week and 6 week marks (arbitrary dates) - check the 5d avg from each of those points
        smap6 = o.mean([float(e[1]) for e in hist[didx+5*6:didx+5*7]]) #6-7 weeks prior to the earnings
        smap2 = o.mean([float(e[1]) for e in hist[didx+5*2:didx+5*3]]) #2-3 weeks prior to the earnings
        ppurch = float(hist[didx+1][1]) #price on the nominal purchase date close (a day before earnings call)
        smad = o.mean([float(e[1]) for e in hist[didx:didx+5]]) #week after the day of the earning
        
        #add to the score if the ratios are similar between each time point and it gains afterwards
        if(abs(smap6/smap2-smac6/smac2) <= tol62 and abs(smap6/ppurch-smac6/cpurch) <= tol6p and abs(smap2/ppurch-smac2/cpurch) <= tol2p):
          if(smad>ppurch*sellUp()): #if subsequent price after call date is >purchPrice with some tolerance
            if(verbose): print(f"similar setup followed by a gain found at {d}")
            score += 1
          elif(smad<ppurch*sellDn()): #if price after call date is <purchPrice with some tolerance
            if(verbose): print(f"similar setup followed by a loss found at {d}")
            score -= 1 #it lost with this pattern, so for sure don't want this one
      else: #date isn't present in the hist
        if(verbose): print(f"{d} not present in the data")
        
      
    rsiTol = float(c[algo]['rsiTol']) #tolerance for the rsi cut off
    #is the rsi in a extreme state?
    if(rsi>=rsiTol): #TODO: ensure this is the correct assumption
      if(verbose): print(f"rsi is sufficient at {round(rsi,2)}")
      score += 1
    else:
      if(verbose): print(f"rsi is not sufficient at {round(rsi,2)}")
    
    #have more hedge funds increased their holdings than decreased?
    if(holdings['increased']['holders']>holdings['decreased']['holders']):
      if(verbose): print("hedge funds are sufficient")
      score += 1
    else:
      if(verbose): print(f"hedge funds are not sufficient")
    
    maxScore = len(earnDates)+1+1 #max possible obtainable score (total earn dates (usually 4)+rsi+holdings)
    if(verbose): print(f"score: {score}, maxScore: {maxScore}")
    
    if(score/maxScore>=float(c[algo]['minScorePct'])): #must reach the cutoff score to be considered a good buy
      goodBuys[e['symbol']] = earnDate
  
  '''
  
  return goodBuys #return dict of {symb:note}


#calculate the rsi based on the most recent history of lenth per (hist is output of getHistory)
def getRSI(hist,per=14):
  if(per<len(hist)): #ensure that there's enough info to calculate it
    difs = [float(hist[i][1])/float(hist[i+1][1]) for i in range(per)] #get the daily changes
    avgGain = o.mean([e for e in difs if e>1])
    avgLoss = o.mean([e for e in difs if e<1])
    rsi = 1-(1/(1+avgGain/avgLoss)) #value between 0 and 1
    return rsi
  else:
    print("not enough info to calculate rsi")
    return 0

#get a list of stocks to be sifted through - format of {date, inf:[data]}
def getUnsortedList(maxTries=3):
  tries=0
  r = []
  while tries<maxTries:
    try:
      date = o.nextTradeDate() if tries>1 else str(o.dt.date.today()) #try getting the data at least twice, then if it still doesn't work, then try looking at the next trade date (this should take care of earnings not being announced on the weekends or holidays)
      r = o.json.loads(o.requests.get(f"https://api.nasdaq.com/api/calendar/earnings?date={date}",headers=o.HEADERS, timeout=5).content)['data']['rows']
      if(r is None): raise("null response") #raise an error if nothing is returned (like on a closed market day)
      break
    except Exception:
      print(f"Error in getting unsorted list for {algo} algo. Trying again...")
      o.time.sleep(3)
      tries+=1
      pass
  return {'date':date,'inf':r}


#where symblist is a list of stocks and the function returns the same stocklist as a dict of {symb:goodsell(t/f)}
def goodSells(symbList):
  prices = o.getPrices([e['symbol']+"|stocks" for e in ul['inf']])
  prices = {s.split("|")[0]:prices[s]['price'] for s in prices} #isolate to {symb:price}
  #return true for all that are present in the price list and poslist and that are outside the triggers (that is, not inside the triggers)
  gs[e] = {e:(e in prices and e in posList and not sellDn()<prices[e]/posList[e]['buyList']<sellUp()) for e in symbList}
  return gs

#TODO: this should also account for squeezing
def sellUp(symb=""):
  mainSellUp = float(c[algo]['sellUp'])
  if(symb in posList):
    sellUp = mainSellUp #TODO: account for squeeze here
  else:
    sellUp = mainSellUp
  return sellUp

#TODO: this should also account for squeezing
def sellDn(symb=""):
  mainSellDn = float(c[algo]['sellDn'])
  if(symb in posList):
    sellDn = mainSellDn #TODO: account for squeeze here
  else:
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(c[algo]['sellUpDn'])
