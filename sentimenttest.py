import pprint
import robin_stocks as r
import caduceus 
from extendBrokers.utilities import robinhoodConfig
from extendBrokers.robinhood import account_details
import pprint
from extendBrokers.utilities import load_config
import json 
from pathlib import Path
import requests
import toml
import re
from bs4 import BeautifulSoup

from pymongo import MongoClient, collation, collection, cursor, database
import datetime


database_url = load_config().mongodb_url
client = MongoClient(database_url)
todays_date = datetime.datetime.now().strftime("%Y_%m_%d")
NEWS_DATABASE  = client.MultiStock
NEWS_COLLECTION = NEWS_DATABASE.todays_news[todays_date]
BING_NEWS = NEWS_COLLECTION.bing_headlines
BLOOMBERG_CDN = NEWS_COLLECTION.bloomberg_cdn



# try:
# 	loging = account_details.loginRohinhood()

# except:
# 	print("Error: Login failed")
# 	exit()


news_file = load_config().news_file



buying_list = load_config().buy_list
with open(buying_list, 'r') as f:
    tickers = json.load(f)
    
def bing_search(tickers):
    bing_searches = {}
    bing_list = []
    links = load_config().news_source
    for link in links:
        if link == "BING_SEARCH":
            url = links[link] + tickers
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            for news_card in soup.find_all('div', class_="news-card-body"):
                title = news_card.find('a', class_="title").text
                article_link = news_card.find('a', class_="title").get('href')
                try:
                    time = news_card.find(
                        'span',
                        attrs={'aria-label': re.compile(".*ago$")}
                    ).text
                    entry = {
                        'ticker': tickers,
                        'title': title,
                        'link': article_link,
                        'time': time
                    }
                    # create a unqiue key for each article
                    # print(entry)

                except:
                    pass
    # print("Bing Search Complete",bing_list)
    # return bing_searches, bing_list

                    # NEWS_COLLECTION.insert_many(entry)

                    # insert_data = database_()
                    # insert_data.insert_one(entry)
                    # data.insert_one(entry)
                    # return entry

                    
                    # with open(news_file, 'a') as f:
                    #     json.dump(entry, f)
                    # bing_list.append(entry)
          






news_file = load_config().news_file
for ticker in tickers['dj']:
    try:
        NEWS_COLLECTION.insert_one({"_id":tickers})
    except Exception as e:
        pass

    for i in NEWS_COLLECTION.find({"_id":ticker}):
        if i['_id'] == ticker:
            NEWS_COLLECTION.update_one({"_id":ticker}, {"$set": {"symbol":ticker}})


            
            # print("\n")
            # bing_search(ticker)
            # print("breakkkkk"
            # )
        # if i == ticker:
        #     print("Already in database")
        #     break

    # if ticker in NEWS_COLLECTION.find({"_id":ticker}):
    #     print("Already in database")

    # if  NEWS_COLLECTION.find({"_id":ticker}) 
    # a.insert_one({"hellow":ticker})



#     article_list = bing_search(tickers = ticker) 
#     print(article_list)
    # with open(news_file, 'w') as f:
    #     json.dump(article_list, f, indent=4)
    # pprint.pprint(article_list)
    # print(article_list)



    #     print(save_urls)
    #     urls.append(save_urls)
    # return save_urls



