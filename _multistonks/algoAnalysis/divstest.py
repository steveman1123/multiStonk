import sys
sys.path.append("./algos")
import divs
#
import datetime as dt
from workdays import workday as wd

divs.init("./configs/multi.config")

today = dt.date.today()
dateList = [str(wd(today,d)) for d in range(0,10)]

#print(dateList)
numDays = 2

for i,d in enumerate(dateList[:-numDays+1]):
  days2check = dateList[i:i+numDays]
  l=divs.goodBuys(divs.getUnsortedList(days2check))
  print(days2check,"\t",len(l))
  