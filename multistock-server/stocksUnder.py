import requests 
import time
import requests
import time 





def get_stocks_under_1(maxTries=3,params_=None):
    symbList = list()
    urlList = ['nasdaq']
    for e in urlList:
        url = f'https://stocksunder1.org/{e}-penny-stocks/'
        tries = 0
        while tries < maxTries:
            try:
                r = requests.post(
                    url, params=params_, timeout=5).text
                pageList = r.split('.php?symbol=')[1:]
                pageList = [e.split('">')[0] for e in pageList]
                symbList += pageList
                maxTries = 3 # if we make it this far, then we should just call it a day
                return symbList
            except Exception:
                print(
                    "No connection, or other error encountered (SU1). Trying again...")
                time.sleep(3)
                tries += 1
                continue