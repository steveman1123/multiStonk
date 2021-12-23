import pprint
import robin_stocks as r
import market_analysis 
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
buy_list = NEWS_DATABASE[todays_date].MultiStock.buying_list
# NEWS_COLLECTION = NEWS_DATABASE.todays_news[todays_date]
# BING_NEWS = NEWS_COLLECTION.bing_headlines
# BLOOMBERG_CDN = NEWS_COLLECTION.bloomberg_cdn



# try:
# 	loging = account_details.loginRohinhood()

# except:
# 	print("Error: Login failed")
# 	exit()


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
                    # print(entry)
                    bing_list.append(entry)
                except:
                    pass
            return bing_list


def first_update(ticker):

    for data_ticker in buy_list.find({"_id":ticker}):
        stock  = data_ticker["_id"]
        bing = bing_search(stock)
        for get_bing in bing:
            if ticker == get_bing['ticker']:
                try:
                    buy_list.update_one(
                        {'_id': get_bing['ticker']},
                        {'$push': {'bing_news': get_bing}}
                    )
                except Exception as e:
                    print(e)
                    pass
                

def check_buying_list():

    for ticker in tickers["dj"]:
        check_id = ({"_id":ticker, "last_updated":todays_date})
        filter_dict = ({'_id':ticker,'added_on':todays_date,'ticker': ticker, 'last_updated':todays_date})
        if buy_list.count_documents({
            '_id':ticker,
            'added_on':todays_date,
            'ticker': ticker}):
            buy_list.update_one(check_id, {'$set': {'last_updated':todays_date}})
            #TODO only update if last_updated is not today and time has passed
            print("Bing Search Complete")
            # pass
        else:
            print("new ticker found")
            try:
                buy_list.insert_one(filter_dict)
                first_update(ticker)
                # first_update()
            except Exception as e:
                print(e)
                pass



check_buying_list()

def routine_update(ticker):
    for data_ticker in buy_list.find({"_id":ticker}):
        stock  = data_ticker["_id"]
        bing = bing_search(stock)
        for get_bing in bing:
            if ticker == get_bing['ticker']:
                try:
                    buy_list.update_one(
                        {'_id': get_bing['ticker']},
                        {'$push': {'bing_news': get_bing}}
                    )
                except Exception as e:
                    print(e)
                    pass

            
