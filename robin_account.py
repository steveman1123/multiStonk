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

headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
get_ip = socket.gethostbyname(socket.gethostname())

keyFile = "./api-keys-dev.txt"

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
        print(ROBINHOOD_USERNAME, ROBINHOOD_PASSWORD, ROBINHOOD_TOTPS)
        account_info = r.robinhood.login(username=ROBINHOOD_USERNAME, password= ROBINHOOD_PASSWORD, mfa_code=TOTPS_TOKEN,store_session=True)
        return account_info
        # print(account_info)
        # bot_token['robinhood_token'] = account_info
    except Exception as e:
        print("Error: ",e)
        exit()


def openPositions():
    #TODO: get positions from robinhood
    # r.robinhood.cancel_all_stock_orders()
    
    symbols = []
    holdings_data = r.robinhood.build_holdings()
    for item in holdings_data:
        if not item:
            continue
        instrument_data = r.robinhood.get_instrument_by_url(item.get('instrument'))
        symbol = instrument_data['symbol']
        symbols.append({'symbol': symbol, 'qty': item['quantity'] })
        
    return symbols


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
            # print("This may be a pending order :" + symbol)
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
        else:
            print("getting real positions :" + symbol)
            #TODO: Come back to this function to fix the relevant info
            return openPositions()
    return positions
            # helded_positions = [{
            #     "symbol": symbol,
            #     "qty": "10",
            #     "unrealized_pl": "-2.4",
            #     "unrealized_plpc": "-0.2620087336244541",
            #     "avg_entry_price": "2.29",
            #     "unrealized_intraday_plpc": "-0.0012"
            # }]
            # return helded_positions




def account_history():
    closing_historical = []
    time_stamp = []
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
    user_account = r.robinhood.account.load_phoenix_account()
    account_info['portfolio_value'] = user_account['equities']['equity']['amount']
    account_info['cash'] = user_account['account_buying_power']['amount']
    return account_info    

 
 
 
def createOrder(side,
                qty,
                symb,
                preference,
                time_in_force="day",
                useExtended=False
                ):
    response_ = {}
    order = {
        "symbol": symb,
        "qty": qty,
        "type": preference['orderType'],
        "side": side,
        "time_in_force": time_in_force,
        "extended_hours": useExtended
    }
    try:
        current_price = r.robinhood.get_latest_price(order['symbol']).pop()
        if order['side']=='sell':
            limit_price = (float(current_price) + float(preference['sell_limit_offset']))
        elif order['side']=='buy':
            limit_price = (float(current_price) - float(preference['buy_limit_offset']))
        # lets hope this is the correct way to do it... 
        print("placing :",order['side'], preference['orderType'] + " " + side + " " + str(qty) + " " + symb)
        current_price = r.robinhood.get_latest_price(order['symbol']).pop()
        # print(limit_price, current_price)
        response_ = r.robinhood.order(
            side = order['side'],
            symbol  = order['symbol'],
            quantity = order['qty'],
            limitPrice = limit_price,
            timeInForce='gtc',
            jsonify=True,
            extendedHours=False
        )
        response_["qty"] = order['qty']
        # print(response_)
        return response_
    except Exception as e:
        print("Error: ",e)
        return response_
        

    
def multistock_server(algo,c=None):
    if algo == "highrisk":
        trending_ = requests.get('http://' + get_ip + ':2010/api/stocktwits-trending/')
        return trending_.json()
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
    
    
    winners = requests.get('http://' + get_ip + ':2010/api/buyholdsell/')
    return winners.json()
    # suggestion_ = requests.get('http://' + get_ip + ':2010/api/stocktwits-suggested/')
    # print( marketwatch.json(), stocksunder.json(), trending_.json(), suggestion_.json())

    


def postWatchlist(payload):
    # print("posting watchlist" + str(payload))
    create_wl = requests.post('http://' + get_ip + ':2010/api/make_watchlist/',headers=headers,data=json.dumps(payload))
    





def del_watchlist(token,wl_name = None):
    blacklisted = ["Options Watchlist","IPO Access"]
    """
    delete all watchlist created in a provide list
    """
    header = {
        'Content-Type': 'application/json; charset=utf-8',
        'X-Robinhood-API-Version': '1.431.4',
        'Authorization': 'Bearer ' + token['token'],
        'X-Minerva-API-Version': '1.100.0',
        'X-Phoenix-API-Version': '0.0.3',
        'X-Nummus-API-Version': '1.41.11',
        'Accept-Encoding': 'gzip,deflate',
        'X-Midlands-API-Version': '1.66.64',
    }
    # TODO: find a way to delete watchlist without sending account info the the server
    all_watchlists = r.robinhood.get_all_watchlists()
    for wl in all_watchlists['results']:
        get_display_name = wl['display_name']
        if get_display_name in blacklisted:
            print("skipping :",get_display_name)
        else:
            watchlist_id = wl['id']
            try:
                delete_watchlist = requests.delete(f'https://api.robinhood.com/midlands/lists/{watchlist_id}/',headers=header)
                print(delete_watchlist.json())
                # return delete_watchlist.json()
            except Exception as e:
                print("def delete_watchlist() api maybe down: ",e)
                continue




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
    message = 'Starting starting...'
    sendmail(message)
    return message


def send_list():
    message = 'Starting sending list...'
    init_robinhood(keyFile)
    with open(systemConfigs['sendPath'], "r") as text_file:
        status_ = text_file.read()
        
        sendmail(message = str(status_),subject=message+" "+str(dt.datetime.now()))
        text_file.close()
    return message
        
# send_list()



