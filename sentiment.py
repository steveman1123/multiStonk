from market_analysis import hermes
# hermes.check_buying_list()
# login to robinhood

import robin_stocks as r
from extendBrokers.robinhood import account_details

try:
	loging = account_details.loginRohinhood()
except:
	print("Error: Login failed")
	exit()



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



# print(unrealized_())



