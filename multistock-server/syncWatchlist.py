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
