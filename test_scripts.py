
import threading
from multistock import updateList
import robin_stocks
from robin_account import account_isValid
from robin_account import postWatchlist,del_watchlist,multistock_server
import requests 
import time
import json




stocks = multistock_server(algo=None,c=None)
for i in stocks:
    if i == "winners":
        print(i, stocks[i])
    if i == "losers":
        print(i,stocks[i])
        
    



# wl_info = {}
# info  = account_isValid()
# wl_info["token"] = info['access_token']
# wl_info["wl_name"] = "testing"
# postWatchlist(payload=wl_info)
# del_watchlist(token=wl_info)
# robin_stocks.robinhood.cancel_all_stock_orders()
# robin_stocks.robinhood.get_watchlist_by_name()
# locking_ = threading.Lock()
# updateList(algo='highrisk',lock = locking_,verbose=True)



# print(access_token)






# trending_ = robin_account.multistock_server(algo="highrisk",c=None)
# print(trending_)
# algo = "highrisk"
# if algo == 'highrisk':
#     algoBuys = eval(algo+".getList(stocklist=trending_)")

