# import os
# import time 
# import json
# import datetime
# import os 
# import robin_stocks
# from pathlib import Path
# import pandas as pd
# import toml



# # from extend_brokers.robinhood.robinhood_account.my_account import get_watchlist_tickers,delete_watchlist_in_list,make_watchlist_in_list
# # from validate_settings.internal_files import internal_checks

# class manage_watchlist:
#     todays_date = str(datetime.date.today())
#     watchlist_settings = Path().absolute() /"backup"/"watchlist"/ f'{todays_date}/watchlist.json'
#     if not watchlist_settings.exists():
#         os.makedirs(watchlist_settings.parent, exist_ok=True)
#         with open(watchlist_settings, 'w') as f:
#             json.dump({}, f, indent=4)
    
            
#     def __init__(self,my_token):
#         self.robinhood_token = my_token
#         # self.watchlist_setting = internal_checks().my_config['watchlist_settings']
#         self.watchlist_list_path  = self.watchlist_settings
#         self.watchlist_list  =  get_watchlist_tickers()
#         self.backup_watchlist_ = self.backup_watchlist()
#         if self.backup_watchlist_ is False:
#             print("no tickers to backup")
#             time.sleep(5)
#         if self.watchlist_list is False:
#             print("Watchlist not found.")
#             self.make_watchlist()
#         else:
#             pass   
#         tiddy_up = self.tiddy_up_watchlist()
#         if tiddy_up is False:
#             print("No tickers where found.")
#         else:
#             print("Tidy up watchlist completed")

#     def backup_watchlist(self):
#         if self.watchlist_list is False:
#             return False
#         else:         
#             for tickers  in self.watchlist_list:
#                 symbol = tickers['symbol']
#                 quotes = robin_stocks.robinhood.get_quotes(inputSymbols=symbol,info="bid_price")
#                 tickers['last_quoted'] = quotes
#                 tickers['backup_date'] = str(self.todays_date)
#                 with open(self.watchlist_list_path, 'a') as f:
#                     json.dump(tickers, f, indent=4)
#                     f.close()
                
    
#     def tiddy_up_watchlist(self):
#         tickers = self.watchlist_list 
#         if tickers is False:
#             return False
#         else:
#             for ticker in tickers:
#                 ticker_symbol = ticker['symbol']
#                 if ticker_symbol is not None:
#                     print("deleting watchlist")
#                 delete_watchlist_in_list(my_token = self.robinhood_token) 
#                 break
             

             
#     def make_watchlist(self):
#         print("Making watchlist")
#         make_watchlist_in_list(my_token = self.robinhood_token)
#         return True
                
