import json
import requests
import robin_stocks

def make_watchlist(token,wl_name=None):
	headers = {

		'Content-Type': 'application/json; charset=utf-8',
		'X-Robinhood-API-Version': '1.431.4',
		'Authorization': 'Bearer ' + token,
		'X-Minerva-API-Version': '1.100.0',
		'X-Phoenix-API-Version': '0.0.3',
		'X-Nummus-API-Version': '1.41.11',
		'Accept-Encoding': 'gzip,deflate',
		'X-Midlands-API-Version': '1.66.64',
	}

	data = {
		"display_name": wl_name,
		# "icon_emoji": icon_emoji

	}
	try:     
		dump_utf = json.dumps(data)
		response = requests.post('https://api.robinhood.com/midlands/lists/', headers=headers, data=dump_utf)
		return response.json()
	except Exception as e:
		return "Error: create_watchlist() api maybe down " + str(e)



def del_watchlist(token,wl_name = None):
    """
    delete all watchlist created in a provide list
    """
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
    # TODO: find a way to delete watchlist without sending account info the the server
    all_watchlists = robin_stocks.robinhood.get_all_watchlists()
    for wl in all_watchlists['results']:
        if wl['display_name'] in wl_name:
            watchlist_id = wl['id']
            try:
                delete_watchlist = requests.delete(f'https://api.robinhood.com/midlands/lists/{watchlist_id}/',headers=header)
                # return delete_watchlist.json()
            
            except Exception as e:
                print("def delete_watchlist() api maybe down: ",e)
                continue
        else:
            continue
    
