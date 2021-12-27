# #get all the trades made from a starting date and get relevent info into a csv file
# #for analyzing win & loss rates

# import alpacafxns as a
# import json, csv
# import datetime as dt

# a.init("../stockStuff/apikeys/steve.txt",0)

# #set up the range
# startDate = "2021-04-20"
# endDate = str(dt.date.today())

# #get the trade data
# print("\ngetting trade data")
# trades = a.getTrades(startDate, endDate)[::-1]

# print("formatting data")
# #formatted as: symbol, date, side, price, qty, cumulative qty, avgBuyPrice (if buy, else blank), win/loss (if sell, else blank)

# tradedSymbs = [] #make a list of the symbols only
# out = [['symbol', 'date', 'side', 'price', 'qty', 'cumqty', 'avgBuyPrice', 'w/l']]
# for t in trades:
#   #get the transaction date
#   try:
#     xtnDate = str(dt.datetime.strptime(t['transaction_time'],"%Y-%m-%dT%H:%M:%S.%fZ").date())
#   except ValueError:
#     xtnDate = str(dt.datetime.strptime(t['transaction_time'],"%Y-%m-%dT%H:%M:%SZ").date())
	
#   #get the numeric values of qty and price
#   qty = int(t['qty'])
#   price = float(t['price'])
	
#   #if it's a buy, then set the params
#   if(t['side']=='buy'):
#     #if it hasn't been bought before
#     if(t['symbol'] not in tradedSymbs):
#       avgBuyPrice = price
#       cumqty = qty

#     #if it's already been bought before
#     else:
#       #get the latest instance of the symbol and the avgBuyPrice and cumulative qty for it
#       latestAvgBuyPrice = out[len(out)-tradedSymbs[::-1].index(t['symbol'])-1][6]
#       cumqty = out[len(out)-tradedSymbs[::-1].index(t['symbol'])-1][5]
#       #calculate the new average buy price
#       avgBuyPrice = (latestAvgBuyPrice*cumqty+price*qty)/(cumqty+qty)
#       #add the new cumulative quantity
#       cumqty += qty
			
#     wl = ""
	
#   #else if it's a sell, then set the params
#   elif(t['side']=='sell'):
#     #if it sells before buying, not enough info is known, so no data
#     if(t['symbol'] not in tradedSymbs):
#       avgBuyPrice = 0
#       cumqty = 0
#       wl = "NA"
#     else:
#       #get the latest instance of the symbol and the avgBuyPrice for it
#       latestAvgBuyPrice = out[len(out)-tradedSymbs[::-1].index(t['symbol'])-1][6]
#       cumqty = out[len(out)-tradedSymbs[::-1].index(t['symbol'])-1][5]
#       #calculate whether it's a winning or losing trade
#       wl = 'w' if price>latestAvgBuyPrice else 'l'
#       #remove the new cumulative quantity
#       cumqty -= qty
#       avgBuyPrice = latestAvgBuyPrice
	
#   #append the symbol to show it's been traded
#   tradedSymbs += [t['symbol']]
	
#   #append the data to the output
#   out += [[t['symbol'],xtnDate,t['side'],price,t['qty'],cumqty,round(avgBuyPrice,4),wl]]

# #for r in out:
# #  print(*r,sep="\t")


# #print("writing to file")
# #writer = csv.writer(open("./tradeData.csv",'w+'),delimiter=',')
# #writer.writerows(out)

# print("calculating wins and loses\n")

# #total wins and loses
# tw = len([e for e in out if e[-1]=="w"])
# tl = len([e for e in out if e[-1]=="l"])

# avgwamt = [e[3]-e[6] for e in out if e[7]=="w"]
# avgwamt = round(sum(avgwamt)/len(avgwamt),3)
# avglamt = [e[3]-e[6] for e in out if e[7]=="l"]
# avglamt = round(sum(avglamt)/len(avglamt),3)

# print(f"total wins:\t{tw}")
# print(f"total loses:\t{tl}")

# print(f"avg win amt:\t{avgwamt}")
# print(f"avg lose amt:\t{avglamt}")

# print(f"win amt:\t{round(tw*avgwamt,3)}")
# print(f"lose amt:\t{round(tl*avglamt,3)}")

# print(f"Net earning:\t{round(tw*avgwamt-abs(tl*avglamt),3)}")



# from math import e
# import pprint
import robin_stocks as r
from extendBrokers.utilities import robinhoodConfig
from extendBrokers.robinhood import account_details
import pprint
# from caduceus.herald import *

# from caduceus.herald as h
try:
	loging = account_details.loginRohinhood()

except:
	print("Error: Login failed")
	exit()





# r.robinhood.orders.cancel_all_stock_orders()



# def createOrder(symbol,shares,side):
# 	"""
# 	create an order for the given side of the trade	(buy or sell)
# 	"""
# 	#such as the order id, the state of order (queued, confired, filled, failed, canceled, etc.), \

# 	limit_parameters = robinhoodConfig().limit_order
# 	if limit_parameters['use_order_limit'] == True:
# 		if side == 'buy':
# 			if limit_parameters['place_limitOders'] == True:
# 				if limit_parameters['remove_fees']:
# 					fees = float(limit_parameters['remove_fee']*100)
# 				get_quote = r.robinhood.get_quotes(symbol,"last_trade_price")
# 				last_quote = float(get_quote.pop())
# 				exclude_fees = last_quote - fees
# 				buy_limit = float(exclude_fees-limit_parameters['buy_limit'])
# 				place_limit_order = r.robinhood.order_buy_limit(symbol, quantity= shares, limitPrice= buy_limit, timeInForce='gtc')
# 				status ={
# 					"status": place_limit_order['state']
# 				}
# 				# print(status)
# 				return status
# 			else:
# 				market_confrimed = r.robinhood.order_buy_market(symbol, quantity= shares, timeInForce='gtc')
# 				market_confrimed_status ={
# 					"status": market_confrimed['state']
# 				}
# 				# print(market_confrimed_status)
# 				return market_confrimed_status
# 		elif side == 'sell':
# 			try:		
# 				if limit_parameters['place_limitOders'] == True:
# 					if limit_parameters['remove_fees']:
# 						fees = float(limit_parameters['remove_fee']*100)
# 					get_quote = r.robinhood.get_quotes(symbol,"last_trade_price")
# 					last_quote = float(get_quote.pop())
# 					exclude_fees = last_quote + fees
# 					sell_limit = float(exclude_fees+limit_parameters['sell_limit'])
# 					place_limit_order = r.robinhood.order_sell_limit(symbol, quantity= shares, limitPrice= sell_limit, timeInForce='gtc')
# 					print(place_limit_order)
# 					sell_status ={
# 						"status": place_limit_order['state']
# 					}
# 					# print(sell_status)
# 					return sell_status
# 				else:
# 					market_confrimed = r.robinhood.order_sell_market(symbol, quantity= shares, timeInForce='gtc')
# 					pprint.pprint(market_confrimed)				
# 					sell_confrimed_status ={
# 						"status": market_confrimed['state']
# 					}
# 					# print(sell_confrimed_status)
# 					return sell_confrimed_status
# 			except:
# 				print("Error: Order failed... ")
# 				return False
# 	else:
# 		print("Error: Order failed... use_order_limit is required")
# 		pass
# r.robinhood.cancel_all_stock_orders()


# import robin_stocks.robinhood as r 

# '''

# This is an example script that will show you how to check the performance of your open positions.
#         "asset_class": "us_equity",
#         "asset_id": "c15f433e-3c3c-4457-973d-ff61e98a8dda",
#         "asset_marginable": "True",
#         "avg_entry_price": "4.56",
#         "change_today": "0",
#         "cost_basis": "9.12",
#         "current_price": "4.12",
#         "exchange": "NASDAQ",
#         "lastday_price": "4.12",
#         "market_value": "8.24",
#         "qty": "2",
#         "side": "long",
#         "symbol": "EVAX",
#         "unrealized_intraday_pl": "0",
#         "unrealized_intraday_plpc": "0",
#         "unrealized_pl": "-0.88",
#         "unrealized_plpc": "-0.0964912280701754"
# '''

# # #!!! Fill out username and password
# # username = ''
# # password = ''
# # #!!!

# # login = r.login(username, password)

# # Query your positions



# def unrealized_():

# 	"""
# 	get the unrealized gain/loss of a user

# 	"""
# 	unrealized_returns = []
# 	equity_change = r.robinhood.build_holdings()
# 	# pprint.pprint(equity_change)
# 	for position in equity_change:
# 		last_trade_ = r.robinhood.get_quotes(position, "last_trade_price")
# 		last_trade_price = last_trade_.pop()
# 		unrealized_plpc = float(last_trade_price)- float(equity_change[position]["average_buy_price"])/float(equity_change[position]["average_buy_price"])

# 		_positions = {
# 			"symbol":position,
# 			"unrealized_plpc": unrealized_plpc,
# 			"unrealized_intraday_plpc": equity_change[position]['equity_change'],
# 			# "unrealized_plpc": position["equity_change"][position],
# 			# "quantity": position["quantity"][position]

# 		}


# 		unrealized_returns.append(_positions)
# 	return unrealized_returns






# # print(unrealized_plpc)
# return unrealized_returns


# # Get Ticker symbols
# tickers = [r.get_symbol_by_url(item["url"]) for item in positions]

# # Get your quantities
# quantities = [float(item["quantity"]) for item in positions]
# tickers = ['EVAX']
# quantities = (2)

# # Query previous close price for each stock ticker
# prevClose = r.get_quotes(tickers, "previous_close")

# # Query last trading price for each stock ticker
# lastPrice = r.get_quotes(tickers, "last_trade_price")

# # Calculate the profit per share
# profitPerShare = [float(lastPrice[i]) - float(prevClose[i]) for i in range(len(tickers))]
# print("Profit per share: " + str(profitPerShare))

# # # Calculate the percent change for each stock ticker
# percentChange = [ 100* profitPerShare[i] / float(prevClose[i]) for i in range(len(tickers)) ]
# print(str(percentChange))
# # Calcualte your profit for each stock ticker
# profit = [profitPerShare[i] * quantities[i] for i in range(len(tickers))]
# print(int(profit))
# # Combine into list of lists, for sorting
# tickersPerf = list(zip(profit, percentChange, tickers))

# tickersPerf.sort(reverse=True)

# print ("My Positions Performance:")
# print ("Ticker | DailyGain | PercentChange")
# for item in tickersPerf:
#   print ("%s %f$ %f%%" % (item[2], item[0], item[1]))

# print ("Net Gain:", sum(profit))

# r.logout()
# r.robinhood.cancel_all_stock_orders()

# Caduceus