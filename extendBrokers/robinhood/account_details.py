import robin_stocks as r
from extendBrokers.utilities import robinhoodConfig
import pyotp
import time
import pprint
import datetime





bot_token = {}
def loginRohinhood():
	login_file  = robinhoodConfig().robinhood_credentials()
	ROBINHOOD_USERNAME = login_file['username']
	ROBINHOOD_PASSWORD = login_file['password']
	ROBINHOOD_MFA = login_file['mfa_code']
	ROBINHOOD_TOTPS = login_file['TOTPS']
	try:
		TOTPS_TOKEN = pyotp.TOTP(ROBINHOOD_TOTPS).now()
		bot_robinhood = r.robinhood.login(username=ROBINHOOD_USERNAME, password= ROBINHOOD_PASSWORD, mfa_code=TOTPS_TOKEN,store_session=False)
		bot_token['robinhood_token'] = bot_robinhood
	except Exception as e:
		print("Error: ",e)
		exit()
	return bot_token



def openPositions():
	"""
	open a position
	"""
	symbols = []
	holdings_data = r.robinhood.get_open_stock_positions()
	for item in holdings_data:
		if not item:
			continue
		instrument_data = r.robinhood.get_instrument_by_url(item.get('instrument'))
		symbol = instrument_data['symbol']
		symbols.append(symbol)
	return symbols




def getPosition():
	"""
	Returns: the symbol for each stock in your portfolio as a list of strings
	"""
	symbols = []
	holdings_data = r.robinhood.get_open_stock_positions()
	for item in holdings_data:
		if not item:
			continue
		instrument_data = r.robinhood.get_instrument_by_url(item.get('instrument'))
		symbol = instrument_data['symbol']
		symbols.append(symbol)
	return symbols


def get_portfolio_symbols():
	"""
	Returns: the symbol for each stock in your portfolio as a list of strings: 
	"""
	open_positions = []
	holdings_data = r.robinhood.get_open_stock_positions()
	for item in holdings_data:
		if not item:
			continue
		# pprint.pprint(item)

		instrument_data = r.robinhood.get_instrument_by_url(item.get('instrument'))
		last_trade_price = r.robinhood.get_quotes(instrument_data['symbol'], "last_trade_price")
		# unrealized_pl = float(last_trade_price.pop())- float(item.get('average_buy_price')),

		# print(float(item.get('average_buy_price')))
		# print(float(last_trade_price.pop()))
		# unrealized_plpc =  float(last_trade_price.pop())- float(item.get('average_buy_price'))/float(item.get('average_buy_price'))

		# print(unrealized_plpc)
		portfolio = {
			"symbol": instrument_data['symbol'],
			"quantity": item.get('quantity'),
			"average_buy_price": item.get('average_buy_price'),
			"market_value": last_trade_price,
			"cost_basis": item.get('average_buy_price'),
			# "unrealized_pl": float(last_trade_price.pop())- float(item.get('average_buy_price')),
			# "unrealized_plpc": float(last_trade_price.pop())- float(item.get('average_buy_price'))/float(item.get('average_buy_price')),

			# "unrealized_plpc": unrealized_plpc,


		}
		open_positions.append(portfolio)
	# print(open_positions)
	return open_positions

#TODO: check this function at the end of this project this week:

def getRobinbood_ProfileHistory():
	"""
	get the profile history of a user
	"""
	closing_equity_list = []
	while True:
		try:
			historicals_=  r.robinhood.get_historical_portfolio(interval="hour", span='month', bounds='regular',info=None)
			# pprint.pprint(historicals_['equity_historicals'])
			for begins_at in historicals_['equity_historicals']:
				closing_equity = begins_at['close_equity']
				# datetime.datetime.strptime(begins_at['begins_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
				closing_equity_list.append(closing_equity)
			break
		except Exception as e:
			print("Robinhood api maybe down:function:getRobinbood_ProfileHistory or timeout",e)
			time.sleep(3)
			continue
	# print(closing_equity_list)
	# print(f"{startDate}  {close_equity}")
	return closing_equity_list




def getRobinhood_Acct():
	"""
	get the user account info
	"""
	while True:
		try:
			user_account_info = r.robinhood.load_portfolio_profile()
			time.sleep(1)
			if user_account_info == None:
				print("Robinhood api maybe down:function:getRobinhood_Acct:user_account_info or timeout")
				time.sleep(1)
			break
		except Exception as e:
			print("Robinhood api maybe down:function:getRobinhood_Acct or timeout",e)
			time.sleep(10)
			continue
	return user_account_info



def unrealized_():
	#TODO : check this function at the end of this project this week swap it with get_portfolio_symbols function.
	unrealized_returns = []
	equity_change = r.robinhood.build_holdings()
	# pprint.pprint(equity_change)
	for position in equity_change:
		last_trade_ = r.robinhood.get_quotes(position, "last_trade_price")
		last_trade_price = last_trade_.pop()
		try:
			unrealized_plpc = float(last_trade_price)- float(equity_change[position]["average_buy_price"])/float(equity_change[position]["average_buy_price"])
			_positions = {
				"symbol":position,
				"unrealized_plpc": unrealized_plpc,
				"unrealized_intraday_plpc": equity_change[position]['equity_change'],
				# "unrealized_plpc": position["equity_change"][position],
				"quantity": equity_change[position]["quantity"],

			}
			unrealized_returns.append(_positions)
		except ZeroDivisionError as e:
			continue
	return unrealized_returns





def createOrder(side,symbol,shares):
	"""
	create an order for the given side of the trade	(buy or sell)
	"""
	#such as the order id, the state of order (queued, confired, filled, failed, canceled, etc.), \
	show_orders_details = True
	limit_parameters = robinhoodConfig().limit_order
	if limit_parameters['use_order_limit'] == True:
		if side == 'buy':
			if limit_parameters['place_limitOders'] == True:
				if limit_parameters['remove_fees']:
					fees = float(limit_parameters['remove_fee']*100)
				get_quote = r.robinhood.get_quotes(symbol,"last_trade_price")
				last_quote = float(get_quote.pop())
				exclude_fees = last_quote - fees
				buy_limit = float(exclude_fees-limit_parameters['buy_limit'])
				limt_buy_market = r.robinhood.order_buy_limit(symbol, quantity= shares, limitPrice= buy_limit, timeInForce='gtc')
				if show_orders_details == True:
					pprint.pprint(limt_buy_market)
				return limt_buy_market
			else:
				buy_market = r.robinhood.order_buy_market(symbol, quantity= shares, timeInForce='gtc')
				if show_orders_details == True:
					pprint.pprint(buy_market)
				return buy_market
		elif side == 'sell':
			try:
				if limit_parameters['place_limitOders'] == True:
					if limit_parameters['remove_fees']:
						fees = float(limit_parameters['remove_fee']*100)
					get_quote = r.robinhood.get_quotes(symbol,"last_trade_price")
					last_quote = float(get_quote.pop())
					exclude_fees = last_quote + fees
					sell_limit = float(exclude_fees+limit_parameters['sell_limit'])
					limit_marketsell = r.robinhood.order_sell_limit(symbol, quantity= shares, limitPrice= sell_limit, timeInForce='gtc')
					if show_orders_details == True:
						pprint.pprint(limit_marketsell)
					return limit_marketsell
				else:
					sell_market = r.robinhood.order_sell_market(symbol, quantity= shares, timeInForce='gtc')
					if show_orders_details == True:
						pprint.pprint(sell_market)
					return sell_market
			except:
				print("Error: Order failed... ")
				return False
	else:
		print("Error: Order failed... use_order_limit is required")
		pass


def sellAll(isManual=1):
	# TODO: this function will be replaced with the liquidate_all_assets function
	pos = unrealized_()
	# orders = getOrders()
	if(len(pos)>0):
		if(isManual):
			doit = input('Sell and cancel all positions and orders (y/n)? ')
		else:
			doit="y"
		if(doit=="y"):
			print("Removing Orders...")
		while True:
			for p in pos:
				print("Selling "+p["quantity"]+" share(s) of "+p["symbol"])
				print("TODO: machine learning to verfiy before selling alll:")
			print("Done Selling.")
			return 1
		else:
			print("Selling cancelled.")
		return 0
	else:
		print("No shares held")
		return 0

# get last month profit
def liquidate_all_assets():
	# get all the stocks

    holdings_data = r.robinhood.get_open_stock_positions()
    for item in holdings_data:
        if not item:
            continue
		# pprint.pprint(item)
        instrument_data = r.robinhood.get_instrument_by_url(item.get('instrument'))
        last_trade_price = r.robinhood.get_quotes(instrument_data['symbol'], "last_trade_price")
        portfolio = {
			"symbol": instrument_data['symbol'],
			"quantity": item.get('quantity'),
        }
        trading_price  = float(last_trade_price.pop())
        limit_sell = trading_price + float(0.0000051)
        # order_sell_limit(symbol, quantity, limitPrice, timeInForce='gtc', extendedHours=False, jsonify=True):
        responds = r.robinhood.orders.order_sell_limit(portfolio['symbol'], portfolio['quantity'], limitPrice= limit_sell, timeInForce='gtc')
        pprint.pprint(responds)



        



# liquidate_all_assets() 

# r.robinhood.orders.cancel_all_stock_orders()

		# unrealized_pl = float(last_trade_price.pop())- float(item.get('average_buy_price')),

		# print(float(item.get('average_buy_price')))
		# print(float(last_trade_price.pop()))
		# unrealized_plpc =  float(last_trade_price.pop())- float(item.get('average_buy_price'))/float(item.get('average_buy_price'))

		# print(unrealized_plpc)
		# 	"average_buy_price": item.get('average_buy_price'),
		# 	"market_value": last_trade_price,
		# 	"cost_basis": item.get('average_buy_price'),