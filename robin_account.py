from cmath import exp
import robin_stocks as r
import json
import pyotp
import time
import datetime as dt
import socket
import requests
import json 
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
import subprocess


shell_scripts_dir = os.path.dirname(os.path.abspath(__file__))
# shell_scripts= os.path.join(shell_scripts_dir, 'scripts')

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
get_ip = socket.gethostbyname(socket.gethostname())
# check if file exists
def server_ip(file_name):
    try:
        with open(file_name):
            return get_ip
    except FileNotFoundError:
        with open(file_name, 'w') as f:
            f.write(str(get_ip))
            return get_ip


def init_robinhood(keyFile):
    global ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD, ROBINHOOD_TOTPS,systemConfigs
    with open(keyFile, "r") as keyFile:
        apiKeys = json.loads(keyFile.read())
        systemConfigs= apiKeys
    ROBINHOOD_USERNAME = apiKeys['username']
    ROBINHOOD_PASSWORD = apiKeys['password']
    ROBINHOOD_TOTPS = apiKeys['TOTPS']
    


def account_isValid():
    try:
        TOTPS_TOKEN = pyotp.TOTP(ROBINHOOD_TOTPS).now()
        account_info = r.robinhood.login(username=ROBINHOOD_USERNAME, password= ROBINHOOD_PASSWORD, mfa_code=TOTPS_TOKEN,store_session=True)
        return account_info
        # print(account_info)
        # bot_token['robinhood_token'] = account_info
    except Exception as e:
        print("Error: ",e)
        exit()

      
def getPrices():
    
    
    pass



def openPositions():
    #TODO: get positions from robinhood
    # r.robinhood.cancel_all_stock_orders()
    
    stocks_holdings = []
    holdings_data = r.robinhood.build_holdings()
    for stocks in holdings_data:
        if not stocks:
            continue
        last_trade_ = r.robinhood.get_quotes(stocks, "last_trade_price")
        last_trade_price = last_trade_.pop()
        try:
            unrealized_plpc = float(last_trade_price)- float(holdings_data[stocks]["average_buy_price"])/float(holdings_data[stocks]["average_buy_price"])
            positions = {
                "avg_entry_price": holdings_data[stocks]["average_buy_price"],
				"symbol":stocks,
				"unrealized_plpc": unrealized_plpc,
				"unrealized_intraday_plpc": holdings_data[stocks]['equity_change'],
				# "unrealized_plpc": position["equity_change"][position],
				"qty": holdings_data[stocks]["quantity"],
                "is_pending": False

			}
            stocks_holdings.append(positions)
        except ZeroDivisionError as e:
            # print("ZeroDivisionError: \n",e)
            continue
        # print(positions)
        return stocks_holdings

def get_positions():
    positions = []
    holdings_data = r.robinhood.get_open_stock_positions()    
    # holdings_data = r.robinhood.build_holdings()
    for item in holdings_data:
        if not item:
            continue
        instrument_data = r.robinhood.get_instrument_by_url(item.get('instrument'))
        symbol = instrument_data['symbol']
        held_shares = item['shares_held_for_buys']
        if item["average_buy_price"] == "0.0000":
            getprice = r.robinhood.get_latest_price(symbol).pop()
            pending_orders = {
                "symbol": symbol,
                "qty": held_shares,
                "is_pending": True,
                "unrealized_pl": "0.00",
                "unrealized_plpc": "0.00",
                "avg_entry_price": float(getprice),
                "unrealized_intraday_plpc": "0.00"
            }
            positions.append(pending_orders)
        
        if item["average_buy_price"] != "0.0000":
            _holdings_data = r.robinhood.build_holdings()
            for stocks in _holdings_data:
                if not stocks:
                    continue
                last_trade_ = r.robinhood.get_quotes(stocks, "last_trade_price")
                last_trade_price = last_trade_.pop()
                try:
                    unrealized_plpc = float(last_trade_price)- float(_holdings_data[stocks]["average_buy_price"])/float(_holdings_data[stocks]["average_buy_price"])
                    heldorders = {
                        "avg_entry_price": _holdings_data[stocks]["average_buy_price"],
                        "symbol":stocks,
                        "unrealized_plpc": unrealized_plpc,
                        "unrealized_intraday_plpc": _holdings_data[stocks]['equity_change'],
                        # "unrealized_plpc": position["equity_change"][position],
                        "qty": _holdings_data[stocks]["quantity"],
                        "is_pending": False
                    }
                    positions.append(heldorders)
                except ZeroDivisionError as e:
                    # print("ZeroDivisionError: \n",e)
                    continue
    return positions

def account_history():
    closing_historical = []
    time_stamp = []
    while True:
        try:
            historicals_ = r.robinhood.get_historical_portfolio(
                interval="day", span='3month', bounds='regular', info=None)
            for account_info in  historicals_['equity_historicals']:
                closing_equity = account_info['adjusted_close_equity']
                closing_historical.append(closing_equity)
                historical_date = account_info['begins_at'].split('T')[0].replace('-', ',')
                _year = int(historical_date.split(',')[0])
                _month = int(historical_date.split(',')[1])
                _day = int(historical_date.split(',')[2])
                _time_stamp = dt.datetime(_year,_month,_day,0,0).timestamp()
                time_stamp.append(_time_stamp)
            break
        except Exception as e:
            print(
                "Robinhood api maybe down:function:account_history() or timeout", e)
            time.sleep(3)
            continue
    return closing_historical,time_stamp




def getPrices(symbList):
    # This function needs to be updated: it is not working properly
    
    max_symbs = 20
    d = []
    for i in range(0,len(symbList),max_symbs):
        symbQuery = symbList[i:min(i+max_symbs,len(symbList))]
        d.extend(r.robinhood.get_fundamentals(symbQuery))
        get_price =  r.robinhood.get_latest_price(symbQuery).pop()
    prices = {}
    for e in d:
        if(e['volume'] is not None and len(e['volume'])>0 and float(get_price) > 0):
            prices[f"{e['symbol']}|stocks"] = {
                    'price':float(get_price),
                    'vol':(float(e['volume'])),
                    'open':float(e['open']),
                }    
    return prices




def getStockInfo(ticker,data=['price']):
    data = [e.lower() for e in data]
    out = {}
    try:
        getinfo = r.robinhood.get_fundamentals(inputSymbols= ticker)
        for item in getinfo:
            if not item:
                continue
            if('mktcap' in data):
                out['mktcap'] = float(item['market_cap'])
            if('price' in data):
                out['price'] = float(r.robinhood.get_latest_price(ticker).pop())
    except Exception as e:
        # print(e)
        out["price"] = 0
        out["mktcap"] = 0
    return out



def get_Account_details():
    account_info = {}
    try:
            
        user_account = r.robinhood.account.load_phoenix_account()
        account_info['portfolio_value'] = user_account['equities']['equity']['amount']
        account_info['cash'] = user_account['account_buying_power']['amount']
        return account_info    
    except Exception as e:
        time.sleep(10)
        print("Error: timeout getting account value. Sleeping \n",e)
        return account_info


def ml_determine_limit(ticker, order_side =None,interval=None,risk=None):
    '''
    interval = '5 Minute', '15 Minute', '30 Minute', '1 Hour', '1 Day', '1 Week'
    risk = ('Low', 'Medium', 'High'))

    '''
    # interval = '1 Day'
    # risk = 'Medium'
    subprocess.call(['bash',shell_scripts_dir + '/kaggle.sh','-p' ,interval,risk,ticker])
    ml_limit = requests.get('http://' + server_ip("./server-ip.txt") + ':2010/api/get_ml_requests/')
    for k,l in ml_limit.json().items():
        if 'ml_request' in k:
            current_price = l['current_price']
            confidence = l['confidence'].replace('*(','').replace('% confident)*','')
            equity = l['equity']
            predicted_price = l['requested_prediction_price']
            sell_price = l['sell_price']
            buy_price = l['buy_price']
            side = l['side']

    print(ml_limit.text)
    return current_price,confidence,equity,predicted_price,sell_price,buy_price,side
                    




def determine_limit(ticker,side=None):
    # buying the lowest price in from the last 1 or 2 days

    holdprice = []
    lastest_price = r.robinhood.get_latest_price(ticker).pop()
    get_history = r.robinhood.get_stock_historicals(
        ticker, interval='5minute', span='week')
    for dates in get_history:
        query_date = dates['begins_at'].split('T')[0]
        today_date = time.strftime("%Y-%m-%d")
        yesterday_date = time.strftime(
            "%Y-%m-%d", time.localtime(time.time() - 86400))
        if query_date != today_date and query_date != (yesterday_date):
            holdprice.append(dates['close_price'])
    for lowest in holdprice:
        if lowest == min(holdprice):
            try:
                buyLimit = lowest
                change_diff = (float(lastest_price) - (float(buyLimit)))
                sell_diff = change_diff * 0.05 + float(lastest_price)
                    # print(lastest_price)
                    # print(test)
                # if change_diff is positive value 
                if change_diff > 0:
                    # print("buyLimit: " + str(buyLimit))
                    # print("lastest_price: " + str(lastest_price))
                    # print("change_diff: " + str(change_diff))
                    # print()
                    return buyLimit
                elif change_diff < 0:
                    # we just use the current price to buy - 0.06%
                    # print(ticker + " using current price to buy with 0.06%")
                    limitbuy = float(lastest_price) - (float(lastest_price) * 0.06)
                    # print("buyLimit: " + str(buyLimit))
                    # print("limitbuy: " + str(limitbuy))
                    # print("change_diff: " + str(change_diff))
                    # print()
                    return limitbuy
                if side == "sell":
                    sell_diff = change_diff * 0.005 + float(lastest_price)
                    return sell_diff
                
                holdprice.clear()
            except Exception as e:
                print(e,ticker)
                pass
            







 
def createOrder(side,
                qty,
                symb,
                preference,
                time_in_force="day",
                useExtended=False
                ):

    order_response = {}
    debug = False
    order = {
        "symbol": symb,
        "qty": qty,
        "type": preference['orderType'],
        "side": side,
        "time_in_force": time_in_force,
        "extended_hours": useExtended
    }
    try:
        if preference['machine_learning'] == '1':
            print("Using machine learning")
            quoted_price,confidence,equity,predicted_price,sell_price,buy_price,action = ml_determine_limit(ticker = symb , order_side = order['side'] ,interval=preference['interval'],risk=preference['risk'])
            if action == 'hold':
                if  order['side'] == 'buy':
                    print("Using buy price from machine learning")
                    limit_order = buy_price
                if order['side'] == 'sell':
                    print("Using predicted_price price")
                    limit_order = predicted_price
            elif order['side'] == 'sell':
                print("Using sell price from machine learning")
                limit_order = sell_price
        elif preference['machine_learning'] == '0':
            limit_order = determine_limit(ticker = symb , side = order['side'])   
        if (debug==False):
            order_response = r.robinhood.order(
            side = order['side'],
            symbol  = order['symbol'],
            quantity = order['qty'],
            limitPrice = limit_order,
            timeInForce='gfd',
            jsonify=True,
            extendedHours=False)
            order_response["qty"] = order['qty']
            current_price = r.robinhood.get_latest_price(order['symbol']).pop()
            print(f"symbol: {symb} limit: {limit_order} side:{side} current_price: {current_price} qty: {qty}")
            return order_response
        
      
        if (debug==True):
            debug_response = {"state": "unconfirmed" ,"qty": "1"}
            return debug_response
    
    
    except Exception as e:
        print("Error: ",e)
        return False
    
        

    
def multistock_server(algo,c=None):
    try:
        if('status' in c and c['status'] == "online"):
            try:
                _online = requests.get('http://' + get_ip + ':2010/')
                if _online.status_code == 200:
                    print("Server is online")
            except Exception as e:
                print("Server is offline")
                return False
    except:
        pass
    if algo == "highrisk":
        buyholdsell = requests.get('http://' + get_ip + ':2010/api/buyholdsell/')
        trending_ = requests.get('http://' + get_ip + ':2010/api/stocktwits-trending/')
        suggestion_ = requests.get('http://' + get_ip + ':2010/api/stocktwits-suggested/')
        # print(suggestion_,trending_,buyholdsell)
        return buyholdsell.json(),trending_.json(),suggestion_.json()
        # return trending_.json()
    if algo == "dj":
        stocksunder_payload = {"price": 5, "volume": 0, "updown": "up"}
        marketwatch_payload = {
                "exchange": "nasdaq",
                "visiblecolumns": "Symbol",
                "pricemin": str(c[algo]['simMinPrice']),
                "pricemax": str(c[algo]['simMaxPrice']),
                "volumemin": str(c[algo]['simMinVol']),
                "partial": "true"
            }
        marketwatch = requests.post('http://' + get_ip + ':2010/api/marketwatch/',headers=headers,data=json.dumps(marketwatch_payload))
        stocksunder = requests.post('http://' + get_ip + ':2010/api/stocksunder/',headers=headers,data=json.dumps(stocksunder_payload))
        return marketwatch.json(),stocksunder.json()
    
    
  
    


def postWatchlist(payload):
    # print("posting watchlist" + str(payload))
    create_wl = requests.post('http://' + get_ip + ':2010/api/make_watchlist/',headers=headers,data=json.dumps(payload))
    





def del_watchlist(token,wl_name = None):
    # print("deleting watchlist " + str(wl_name))
    header = {
        'Content-Type': 'application/json; charset=utf-8',
        'X-Robinhood-API-Version': '1.431.4',
        'Authorization': 'Bearer ' + token,
        'X-Minerva-API-Version': '1.100.0',
        'X-Phoenix-API-Version': '0.0.3',
        'X-Nummus-API-Version': '1.41.11',
        'Accept-Encoding': 'gzip,deflate',
        'X-Midlands-API-Version': '1.66.64',
    }
    blacklisted = ["Options Watchlist","IPO Access"]
    try:
        all_watchlists = r.robinhood.get_all_watchlists()
        watchlist_id = ''
        for wl in all_watchlists['results']:
            if wl['display_name'] == wl_name:
                watchlist_id = wl['id']
                delete_watchlist = requests.delete(f'https://api.robinhood.com/midlands/lists/{watchlist_id}/',headers=header)
                # print(delete_watchlist.json())
    except Exception as e:
        print(e)
        pass



def sendmail(message,subject=None):
    msg = MIMEMultipart()
    msg['From'] = systemConfigs['from']
    msg['To'] = systemConfigs['to']
    if subject:
        msg['Subject'] = subject
    else:
        msg['Subject'] = systemConfigs['subject']
    message = str(''.join(message))
    msg.attach(MIMEText(message))
    mailserver = smtplib.SMTP('smtp.mail.me.com', 587)
    # identify ourselves
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login(systemConfigs['from'], systemConfigs['email_password'])
    mailserver.sendmail(systemConfigs['from'],
                        systemConfigs['to'], msg.as_bytes())

    mailserver.quit()
    

def starting():
    init_robinhood(keyFile = "./api-keys-dev.txt")
    message = 'Starting starting...'
    sendmail(message)
    return message


def send_list():
    message = 'Starting sending list...'
    init_robinhood(keyFile = "./api-keys-dev.txt")
    with open(systemConfigs['sendPath'], "r") as text_file:
        status_ = text_file.read()
        
        sendmail(message = str(status_),subject=message+" "+str(dt.datetime.now()))
        text_file.close()
    return message
        
# send_list()



