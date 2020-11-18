import alpacafxns as a

'''
get 60 day, 30 day, and 10 day moving averages
determine if curprice is < or > each
give a strong/weak buy/sell if < or > 0, 1, 2, or 3 of the averages
'''


def main():
  #get symbols
  
  #get symbol history

  ma60 = 0 #moving 60 day avg
  ma30 = 0 
  ma10 = 0

  curPrice = a.getPrice(symb)

  tradability = (curPrice>ma60)+(curPrice>ma30)+(curPrice>ma10)

#should also incorportate looking at history more to determine when a good trade price happens
#something like when the derivitive of price adjusted to the avgs=0

  select tradability:
    case 0:
      strong buy
    case 1:
      weak buy
    case 2:
      weak sell
    case 3:
      strong sell
