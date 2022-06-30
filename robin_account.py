import robin_stocks as r
import json
import pyotp
import time
import pprint
import datetime as dt
from datetime import timezone

def init_robinhood(keyFile):
    global ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD, ROBINHOOD_TOTPS
    with open(keyFile, "r") as keyFile:
        apiKeys = json.loads(keyFile.read())
    ROBINHOOD_USERNAME = apiKeys['username']
    ROBINHOOD_PASSWORD = apiKeys['password']
    ROBINHOOD_TOTPS = apiKeys['TOTPS']
    
    


def account_isValid():
    try:
        TOTPS_TOKEN = pyotp.TOTP(ROBINHOOD_TOTPS).now()
        account_info = r.robinhood.login(username=ROBINHOOD_USERNAME, password= ROBINHOOD_PASSWORD, mfa_code=TOTPS_TOKEN,store_session=True)
        # print(account_info)
        # bot_token['robinhood_token'] = account_info
    except Exception as e:
        print("Error: ",e)
        exit()


def openPositions():
    symbols = []
    holdings_data = r.robinhood.get_open_stock_positions()
    for item in holdings_data:
        if not item:
            continue
        instrument_data = r.robinhood.get_instrument_by_url(item.get('instrument'))
        symbol = instrument_data['symbol']
        symbols.append({'symbol': symbol, 'qty': item['quantity'] })
        
    return symbols


def get_positions():
    #TODO: get positions from robinhood
    template_data = [{
        "symbol": "OBSV",
        "qty": "10",
        "unrealized_pl": "-2.4",
        "unrealized_plpc": "-0.2620087336244541",
        "avg_entry_price": "2.29",
        "unrealized_intraday_plpc": "-0.0012"
        
    }]
    return template_data
    # equity_change = r.robinhood.build_holdings()
    # pprint.pprint(equity_change)
    # for position in equity_change:
    #     print(position)
        
    #     pass


def account_history():
    closing_historical = []
    time_stamp = []
    # time_stamp = []
    while True:
        try:
            historicals_ = r.robinhood.get_historical_portfolio(
                interval="day", span='3month', bounds='regular', info=None)
            # pprint.pprint(historicals_['equity_historicals'])
            # break
            for account_info in  historicals_['equity_historicals']:
                closing_equity = account_info['adjusted_close_equity']
                closing_historical.append(closing_equity)
                historical_date = account_info['begins_at'].split('T')[0].replace('-', ',')
                _year = int(historical_date.split(',')[0])
                _month = int(historical_date.split(',')[1])
                _day = int(historical_date.split(',')[2])
                _time_stamp = dt.datetime(_year,_month,_day,0,0).timestamp()
                time_stamp.append(_time_stamp)
                # print(_time_stamp)
                            
                

            # return closing_historical,_time_stamp
            break
        except Exception as e:
            print(
                "Robinhood api maybe down:function:account_history() or timeout", e)
            time.sleep(3)
            continue
    return closing_historical,time_stamp




def getProfileHistory():
    # portHist = a.getProfileHistory(str(dt.date.today()), '1M')['equity']

    pass


def get_Account_details():
    account_info = {}
    user_account = r.robinhood.account.build_user_profile()
    account_info['portfolio_value'] = user_account['equity']
    account_info['cash'] = user_account['cash']   
    return account_info    

 


def createOrder(side,
                qty,
                symb,
                preference,
                # orderType="market",
                time_in_force="day",
                useExtended=False,
                maxTries=3,
                verbose=False):
    response_ = {}
    order = {
        "symbol": symb,
        "qty": qty,
        "type": preference['orderType'],
        "side": side,
        "time_in_force": time_in_force,
        "extended_hours": useExtended
    }
    if order['side']=='sell':
        print("placing :",order['side'], preference['orderType'] + " " + side + " " + str(qty) + " " + symb)
        current_price = r.robinhood.get_latest_price(order['symbol']).pop()
        limit_price = (float(current_price) + float(preference['sell_limit_offset']))
        response_ = r.robinhood.order(
            side = order['side'],
            symbol  = order['symbol'],
            quantity = order['qty'],
            limitPrice = limit_price,
            timeInForce='gfd',
            jsonify=True,
            extendedHours=False
        )
        print(response_)
        return response_
    if order['side']=='buy':
        print("placing :",order['side'], preference['orderType'] + " " + side + " " + str(qty) + " " + symb)
        current_price = r.robinhood.get_latest_price(order['symbol']).pop()
        limit_price = (float(current_price) - float(preference['buy_limit_offset']))
        response_ = r.robinhood.order(
            side = order['side'],
            symbol  = order['symbol'],
            quantity = order['qty'],
            limitPrice = limit_price,
            timeInForce='gfd',
            jsonify=True,
            extendedHours=False
        )
        print(response_)
        return response_