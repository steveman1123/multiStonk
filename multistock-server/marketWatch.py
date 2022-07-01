import requests 
import time
import requests
import time 




def get_stock(maxTries=3,params=None):
    symbList = list()
    url = "https://www.marketwatch.com/tools/screener/stock"
    skip = 0
    params['skip'] = skip
    tries = 0
    while tries < maxTries:
        try:
            r = requests.get(url, params=params, timeout=5).text
            # print(r)
            pageList = r.split('j-Symbol ">')[1:]
            pageList = [e.split(">")[1][:-3] for e in pageList]
            symbList += pageList
            tries = 3
            return symbList
        except Exception:
            tries += 1
            time.sleep(3)
            return "Error getting MW data . Trying again..."
    skip += len(pageList)


# marketwatch()