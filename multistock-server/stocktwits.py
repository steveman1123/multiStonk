import requests

def stocktwits_trending():
    # trending_stocks.clear()
    trending_stocks = list()
    cookies = {}
    headers = {
        'User-Agent': 'StockTwits/4.23.2 (iPhone; iOS 14.0; Scale/3.00)',
        'Accept-Language': 'en-US;q=1',
        'Authorization': 'OAuth 3fe3a288b178e94a73a4fc3d78b36fca82ed2e20',
        'Accept-Encoding': 'gzip, identity',
    }

    response = requests.get(
        'https://api.stocktwits.com/api/2/streams/trending.json', headers=headers, cookies=cookies)
    get_symbols = response.json()
    trending_stocks.clear() # just incase the list is not empty
    try:
        for line in get_symbols['messages']:
            for symbol in line['symbols']:
                sym = symbol['symbol']
                crypto_ = ".X"
                if sym.endswith(crypto_):
                    sym = sym[:-len(crypto_)]
                else:
                    pass
            trending_stocks += [sym]
        return trending_stocks
    except:
        return "error from function stockstwit_trending_stocks"
        # print("done from function stockstwit_trending_stocks")

def stocktwits_suggested():
    suggested = list()
    cookies = {

    }

    headers = {
        'User-Agent': 'StockTwits/4.23.2 (iPhone; iOS 14.0; Scale/3.00)',
        'Accept-Language': 'en-US;q=1',
        'Authorization': 'OAuth 3fe3a288b178e94a73a4fc3d78b36fca82ed2e20',
        'Accept-Encoding': 'gzip, identity',
    }

    response = requests.get(
        'https://api.stocktwits.com/api/2/streams/suggested.json', headers=headers, cookies=cookies)
    get_symbols = response.json()
    suggested.clear() # just incase the list is not empty
    try:
        for line in get_symbols['messages']:
            try:
                for symbol in line['symbols']:
                    sym = symbol['symbol']
                    crypto_ = ".X"
                    if sym.endswith(crypto_):
                        sym = sym[:-len(crypto_)]
                else:
                    pass
                suggested += [sym]
            except KeyError as e:                
                # print(e)
                continue
        return suggested
    except:
        return "error from function suggested_stocks"

