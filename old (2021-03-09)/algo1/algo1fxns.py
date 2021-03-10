#functions specific to algo1

#checks whether something is a good buy or not (if not, return why - no initial jump or second jump already missed).
#if it is a good buy, return initial jump date
#this is where the magic really happens
#TODO: this should move to algo1
def goodBuy(symb,days2look=c['simDays2look']): #days2look=how far back to look for a jump
  validBuy = "NA" #set to the jump date if it's valid
  if isTradable(symb):
    #calc price % diff over past 20 days (current price/price of day n) - current must be >= 80% for any
    #calc volume % diff over average past some days (~60 days?) - must be sufficiently higher (~300% higher?)
    
    days2wait4fall = c['simWait4fall'] #wait for stock price to fall for this many days
    startDate = days2wait4fall+c['simStartDateDiff'] #add 1 to account for the jump day itself
    firstJumpAmt = c['simFirstJumpAmt'] #stock first must jump by this amount (1.3=130% over 1 day)
    sellUp = c['simSellUp'] #% to sell up at
    sellDn = c['simSellDn'] #% to sell dn at
    
    #make sure that the jump happened in the  frame rather than too long ago
    volAvgDays = c['simVolAvgDays'] #arbitrary number to avg volumes over
    checkPriceDays = c['simChkPriceDays'] #check if the price jumped substantially over the last __ trade days
    checkPriceAmt = c['simChkPriceAmt'] #check if the price jumped by this amount in the above days (% - i.e 1.5 = 150%)
    volGain = c['simVolGain'] #check if the volume increased by this amount during the jump (i.e. 3 = 300% or 3x, 0.5 = 50% or 0.5x)
    volLoss = c['simVolLoss'] #check if the volume decreases by this amount during the price drop
    priceDrop = c['simPriceDrop'] #price should drop this far when the volume drops
    
    start = str(dt.date.today()-dt.timedelta(days=(volAvgDays+days2look)))
    end = str(dt.date.today())
    dateData = getHistory(symb, start, end)
    
    if(startDate>=len(dateData)-2): #if a stock returns nothing or very few data pts
      validBuy = "Few data points available"
    else:
      validBuy = "initial jump not found"
      while(startDate<min(days2look, len(dateData)-2) and float(dateData[startDate][1])/float(dateData[startDate+1][1])<firstJumpAmt):
        startDate += 1
        
        #if the price has jumped sufficiently for the first time
        if(float(dateData[startDate][1])/float(dateData[startDate+1][1])>=firstJumpAmt):
          
          avgVol = sum([int(dateData[i][2]) for i in range(startDate,min(startDate+volAvgDays,len(dateData)))])/volAvgDays #avg of volumes over a few days
          
          lastVol = int(dateData[startDate][2]) #the latest volume
          lastPrice = float(dateData[startDate][4]) #the latest highest price
  
          if(lastVol/avgVol>volGain): #much larger than normal volume
            #volume had to have gained
            #if the next day's price has fallen significantly and the volume has also fallen
            if(float(dateData[startDate-days2wait4fall][4])/lastPrice-1<priceDrop and int(dateData[startDate-days2wait4fall][2])<=lastVol*volLoss):
              #the jump happened, the volume gained, the next day's price and volumes have fallen
              dayPrice = lastPrice
              i = 1 #increment through days looking for a jump - start with 1 day before startDate
              # check within the the last few days, check the price has risen compared to the past some days, and we're within the valid timeframe
              while(i<=checkPriceDays and lastPrice/dayPrice<checkPriceAmt and startDate+i<len(dateData)):
                dayPrice = float(dateData[startDate+i][4])
                i += 1
              
              if(lastPrice/dayPrice>=checkPriceAmt): #TODO: read through this logic some more to determine where exactly to put sellDn
                #the price jumped compared to both the previous day and to the past few days, the volume gained, and the price and the volume both fell
                #check to see if we missed the next jump (where we want to strike)
                missedJump = False
                validBuy = "Missed jump"
                for e in range(0,startDate):
                  # print(str(dateData[e])+" - "+str(float(dateData[e][4])/float(dateData[e+1][1])) +" - "+ str(sellUp))
                  if(float(dateData[e][4])/float(dateData[e+1][1]) >= sellUp): #compare the high vs previous close
                    missedJump = True
                if(not missedJump):
                  validBuy = dateData[startDate][0] #return the date the stock initially jumped
    
  return validBuy #return a dict of valid stocks and the date of their latest jump
  


#the new version of the getGainers function - uses the new functions getList, getHistory, and goodBuy
#TODO: this should move to algo1
def getGainers(symblist):
  gainers = {}
  
  for i,e in enumerate(symblist):
    b = goodBuy(e)
    try:
      gainers[e] = [b, (dt.datetime.strptime(b,"%m/%d/%Y")+dt.timedelta(days=(7*5))).strftime("%m/%d/%Y")]
      print(f"({i+1}/{len(symblist)}) {e} - {b} - {gainers[e][1]}")
    except Exception:
      pass
  #TODO: once getDrugList() is finished, append the returned list to gainers
  return gainers
