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
    


#return dict of good buys of format {symb:note}
#where the note contains the earnings date
def getList(verbose=True):

  
  #each check will add or subtract from a score  (as lacking one or more of the indicators isn't necessarily a dealbreaker)
  if(verbose): print(f"getting unsorted list for {algo}...")
  ul = getUnsortedList() #format of {date, inf:{lastYrRpt,lastYrEPS,time,symb,name,mktcap,fiscQuartEnd,epsFrcst,numEsts}}
  if(verbose): print(f"finding stocks for {algo}...")
  gb = goodBuys(ul)
  if(verbose): print(f"{len(gb)} found for {algo}.")
 
  return gb #return dict of {symb:note}


#get a list of stocks to be sifted through - format of {date:yyyy-mm-dd, inf:[data]}
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
      print(f"Error in getting unsorted list for {algo} algo on {date}. Trying again...")
      o.time.sleep(3)
      tries+=1
      pass
  return {'date':date,'inf':r}

#where symbList should be the output of getUnsortedList() - dict of format {date:yyyy-mm-dd, inf:[data]}
#return dict of format {symb:note} for all symbs that are good buys
def goodBuys(symbList,verbose=False):
  maxPrice = float(c[algo]['maxPrice']) #max price point
  minPrice = float(c[algo]['minPrice']) #min price point
  
  earnDate = symbList['date'] #get the date before it's stripped off

  getPriceList = [e['symbol']+"|stocks" for e in symbList['inf']]
  prices = o.getPrices(getPriceList)
  prices = {s.split("|")[0]:prices[s]['price'] for s in prices} #isolate to {symb:price}
  symbList = [e for e in symbList['inf'] if(e['symbol'] in prices and minPrice<=prices[e['symbol']]<=maxPrice)] #only keep elements that are in prices and within our price range
  
  #check expectations (price increasing in the last month/week, sentiment of articles/blogs/comments, whisper numbers (compared to analyst))
  histWeight = float(c[algo]['histWeight']) #weight to ascribe to the history check
  minConf = float(c[algo]['minConf']) #minimum confidence to have to consider a good buy
  minExpec = float(c[algo]['minExpec']) #minimum expectation to have to consider a good buy (must be high expectation)
  gb = {}
  if(verbose): print(f"{len(symbList)} potential earners found")
  for symb in symbList:
    symb = symb['symbol']
    if(verbose): print("\n"+symb)
    
    #get the analyst target price
    tgtPriceInf = o.getTargetPrice(symb)
    if('consensusOverview' in tgtPriceInf):
      tgtPriceInf = tgtPriceInf['consensusOverview']
    else: #sometimes there may not be any data, so init with everything as 0
      tgtPriceInf = {"lowPriceTarget":0,"highPriceTarget":0,"priceTarget":0,"buy":0,"sell":0,"hold":0}
    tgtPrice = tgtPriceInf['priceTarget']
    if(verbose): print(f"price:\t\t{prices[symb]}")
    if(verbose): print(f"tgtPrice:\t{tgtPrice}")
    
    hist = o.getHistory(symb)
    
    #history must be>7 weeks (to get the 6wk sma) and target price must be > than current price to continue
    if(len(hist)>5*7 and tgtPrice>prices[symb]):
      
      #check the price changes between 6wk sma, 2wk sma, and now
      wk6 = o.mean([float(e[1]) for e in hist[5*6:5*7]]) #get the sma from 6 weeks ago
      wk2 = o.mean([float(e[1]) for e in hist[5*2:5*3]]) #get the sma from 2 weeks ago
      now = prices[symb] #get the most recent price
      
      #assign the history score according to the table based on previous values
      if(now<=wk2<=wk6): histChangeNum = -1
      elif(now<=wk6<=wk2): histChangeNum = -.6
      elif(wk2<=now<=wk6): histChangeNum = .6
      elif(wk2<=wk6<=now): histChangeNum = .3
      elif(wk6<=now<=wk2): histChangeNum = -.3
      elif(wk6<=wk2<=now): histChangeNum = 1
      else: histChangeNum = 0
      
      if(verbose): print(f"histChangeNum:\t{histChangeNum}")
      
      #check total number of reports from the company in the last quarter (more total news is good, even better if + sent)
      # ndaqh = ns.scrapeNDAQ(symb,headNum=25)
      # yfh = ns.scrapeYF(symb)
      # ddgh = ns.scrapeDDG(symb)
      # 
      # print(o.json.dumps(ndaqh,indent=2))
      # print()
      # print(o.json.dumps(yfh,indent=2))
      # print()
      # print(o.json.dumps(ddgh,indent=2))
      # 
      # #get the total number of articles between the two sources
      # totalArts = len(ndaqh)+len(yfh)+len(ddgh)
      
      '''
      include sent of articles for expec, num of articles for conf
      
      rating text for expec (convert to scaled # -1 to 1)
      tgtPrice for expec
      inst for expec
      inside for expec
      hist for expec (1 if today>2wk>6wk, -1 if today<2wk<6wk, )
      
      expec = ratingConvertedToScaledNumber +
              (tgtBuy-tgtSell)/(tgtBuy+tgtSell) +
              (instBuy-instSell)/(instBuy+instSell) +
              (insideBuy-insideSell)/(insideBuy+insideSell) +
              histChngConvertedToScaledNumber
              
      
      rsi for conf
      rating numeric for conf
      num of tgtPrice for conf
      num of inst for conf
      num of inside for conf
      hist weight for conf
      '''
      
      
      #get what the analysts are saying (if anything)
      ratingInf = o.getRating(symb)
      maxRaters = 16 #maximum number of rating institutions (might be more, but this is the highest I've seen)
      possibleRatings = ['underperform','hold','buy','strong buy'] #probably not all values, just the ones I've seen
      if(len(ratingInf)>0 and ratingInf[0].lower() in possibleRatings):
        ratingNum = possibleRatings.index(ratingInf[0].lower())/int(len(possibleRatings)/2)-1 #scale to be -1 to 1
      else:
        ratingNum = 0 #if no rating is found, default to no value
  
      if(verbose): print(f"ratingNum:\t{ratingNum}")

      #get buy count from tgtPriceInf
      [tgtBuy,tgtSell,tgtHold] = [tgtPriceInf['buy'],tgtPriceInf['sell'],tgtPriceInf['hold']]
      
      #get the rsi value
      rsi = o.getRSI(hist)
      
      if(verbose): print(f"rsi:\t\t{round(rsi,3)}")

      
      #get the institutional activity (more recent buying is good)
      instact = o.getInstAct(symb)
      
      [instBuy,instSell,instHold] = [instact['increased']['shares'],instact['decreased']['shares'],instact['held']['shares']]
      
      #check insider trading (many recent buys is good, many recent sells is bad)
      insider = o.getInsideTrades(symb)
      if(len(insider)>0):
        [insideBuy,insideSell] = [int(insider['numberOfSharesTraded']['rows'][0]['months3'].replace(',','')),int(insider['numberOfSharesTraded']['rows'][1]['months3'].replace(',',''))]
      else:
        [insideBuy,insideSell]=[0,0]
        
      #stock should go up if expectations are high and target is reached
      #expectation value should be based on ration of +/- sent for articles, rsi should be neither oversold or overbought, and inside and institutional should both be buy (or really even just institutional should be buy? Unless there's a lot of inside buying in the last week or two)
      expecList = [ratingNum,histChangeNum]
      
      #every element in confList must be between 0 and 1
      confList = []
      if(len(ratingInf)>0 and maxRaters>0): confList.append(ratingInf[1]/maxRaters)
      confList.append(histWeight)
      confList.append(.3<rsi<.7)
      
      if((tgtBuy+tgtSell+tgtHold)>0):
        expecList += [(tgtBuy-tgtSell)/(tgtBuy+tgtSell+tgtHold)]
        confList += [1] #[tgtBuy+tgtSell+tgtHold] #TODO: this should be a ratio
      if((instBuy+instSell)>0):
        expecList += [(instBuy-instSell)/(instBuy+instSell)]
        confList += [1] #[instBuy+instSell] #TODO: this should be a ratio
      if((insideBuy+insideSell)>0):
        expecList += [(insideBuy-insideSell)/(insideBuy+insideSell)]
        confList += [1] #[insideBuy+insideSell] #TODO: this should be a ratio
      
      expec = sum(expecList)/len(expecList) #average out the expectations to get an expecation value between -1 and 1
      conf = sum(confList)/len(confList) #average out the confidence to get a confidence level between 0 and 1

      if(verbose): print(f"expec:\t\t{round(expec,3)}")
      if(verbose): print(f"conf:\t\t{round(conf,3)}")

      
      
      #sellUp/dn should be defined by the expected price/buyPrice and some % of that (so if sellDn is set to be 50% of sellUp, and the expected gain is 10%, then sellUp=1.1 and sellDn=0.95) (store predicted price in note along with earnDate in format of "note": "yyyy-mm-dd, $.$$")
      if(conf>minConf and expec>minExpec):
        gb[symb] = f"{earnDate}, {tgtPrice}"
        if(verbose): print(f"{symb} is a good buy")
      else:
        if(verbose): print(f"{symb} is not a good buy")
        

    
  return gb
  
  

#multiplex the good sell function to return dict of {symb:-1|0|1}
def goodSells(symbList,verbose=False):
  lock = o.threading.Lock()
  lock.acquire()
  posList = o.json.loads(open(c['file locations']['posList'],'r').read())['algos'][algo]
  lock.release()
  
  if(verbose): print(f"stocks in {algo}: {list(posList)}\n")
  symbList = [e.upper() for e in symbList if e.upper() in posList] #make sure they're the ones in the posList only
  buyPrices = {e:float(posList[e]['buyPrice']) for e in symbList} #get the prices each stock was bought at
  if(verbose): print(f"stocks in the buyPrices: {list(buyPrices)}")
  prices = o.getPrices([e+"|stocks" for e in symbList]) #get the vol, current and opening prices
  prices = {e.split("|")[0]:prices[e] for e in prices} #convert from symb|assetclass to symb
  
  if(verbose): print(f"stocks in prices: {list(prices)}")
  #check that it has exceeded the stopLoss or takeProfit points
  gs = {}
  for s in symbList:
    if(s in prices):
      if(verbose): print(f"{s}\topen: {round(prices[s]['price']/prices[s]['open'],2)}\tbuy: {round(prices[s]['price']/buyPrices[s],2)}\tsellUp: {sellUp(s)}\tsellDn: {sellDn(s)}")
      #check if price triggered up
      if(prices[s]['open']>0 and buyPrices[s]>0):
        if(prices[s]['price']/prices[s]['open']>=sellUp(s) or prices[s]['price']/buyPrices[s]>=sellUp(s)):
          gs[s] = 1
        #check if price triggered down
        elif(prices[s]['price']/prices[s]['open']<sellDn(s) or prices[s]['price']/buyPrices[s]<sellDn(s)):
          gs[s] = -1
        else: #price didn't trigger either side
          gs[s] = 0
      else:
        gs[s] = 0
    else:
      gs[s] = 0  
  
  return gs


#TODO: add comments
def sellUp(symb=""):
  if(symb in posList):
    buyPrice = posList[symb]['buyPrice']
    tgtPrice = float(posList[symb]['note'].split(",")[1])
    sellUpAdjustment = float(c[algo]['sellUpAdjustment'])
    sellUp = 1+(tgtPrice/buyPrice-1)*sellUpAdjustment
  else:
    sellUp = float(c[algo]['sellUp'])
  return sellUp

#TODO: add comments
def sellDn(symb=""):
  if(symb in posList):
    sellDnPerc = c[algo]['sellDnPerc']
    sellDn = 1-(sellUp(symb)-1)*sellDnPerc
  else:
    mainSellDn = float(c[algo]['sellDn'])
    sellDn = mainSellDn
  return sellDn

def sellUpDn():
  return float(c[algo]['sellUpDn'])



  
  
  




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

'''
prediction:
expectations  target reached  result
high          no              down
high          yes             up
low           no              up?
low           yes             down?



hist change value:
low med high  buy strength
now 2wk 6wk   -1
now 6wk 2wk   -.6
2wk now 6wk   .6
2wk 6wk now   .3
6wk now 2wk   -.3
6wk 2wk now   1

'''

'''
possible patterns to look for:
consistant changes after every earning report (depending on a hit or miss eps)
consistant hit or miss of eps prediction
consistant large swings in either direction
price action leading up to earnings (consistant for previous reports)



how to format an output:
we want to display price history, earnings dates, eps in comparison to expected
also "whisper" eps:
  (q1pe * q2pe * q3pe)/ 3 = q4pe
  q4price/q4pe = q4eps
should compare top 10 gainers and top 10 losers and everyone else in their own plots (3 total plots)


maybe just want to rephrase things to just look for large changes in the upcoming days/weeks, then just set stop losses and take profits? Ignore anything beyond that until later?
'''
