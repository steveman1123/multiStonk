from extendBrokers.utilities import load_config
import json 
from pathlib import Path
import requests
import re
from bs4 import BeautifulSoup
from pymongo import MongoClient, collation, collection, cursor, database
import datetime
import pprint
import datetime


database_url = load_config().mongodb_url
client = MongoClient(database_url)
todays_date = datetime.datetime.now().strftime("%Y_%m_%d")
NEWS_DATABASE  = client.MultiStock
buy_list = NEWS_DATABASE[todays_date].MultiStock.buying_list

# try:
# 	loging = account_details.loginRohinhood()

# except:
# 	print("Error: Login failed")
# 	exit()


buying_list = load_config().buy_list
with open(buying_list, 'r') as f:
    tickers = json.load(f)
    # close(buying_list)
    f.close()
    
def bing_search(tickers):
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


def bloomberg_current(ticker,country = None):

    if country is None:
        country = "US"
    # for ticker_symbol in ticker:
        print(ticker)
        cookies = {
        }

        headers = {
            'If-None-Match': '"*"',
        }
        
        params = (
            ('template', 'STOCK'),
            ('id', f'{ticker}:{country}'),
        )
        params_updated = (
            ('contentCliff', 'false'),
        )
        response = requests.get('https://cdn-mobapi.bloomberg.com/wssmobile/v1/security/stories', headers=headers, params=params, cookies=cookies)
        bloomberg_articles = response.json()
        # print(f"searching for: {ticker}")
        for article in bloomberg_articles['stories']:
            card = article['card']
            published_date = article['published']
            article_day = datetime.datetime.fromtimestamp( int(published_date))
            article_day_published = article_day.strftime("%Y-%m-%d")
            stories_title = article['title']
            stories_link = article['links']['self']['href']
            if card == "article":
                text_append = []
                internal_id = article['internalID']
                article_updated = requests.get(f'https://cdn-mobapi.bloomberg.com/{stories_link}', headers=headers, params=params_updated, cookies=cookies)
                article_updated_json = article_updated.json()
                for items_text in article_updated_json['components']:
                    for keys,value in items_text.items():
                        if keys == 'parts':
                            for parts_text in value:
                                for fucking_text, pwned_fucking_text in parts_text.items():
                                    if fucking_text == 'text':
                                        if pwned_fucking_text is not None:
                                            # join \n together to make it easier to read
                                            text_append.append(pwned_fucking_text.replace("\n", " "))
                                        else:
                                            text_append.append("")
                text_append = " ".join(text_append)
                return text_append, internal_id, stories_title, stories_link, article_day_published




def first_update(ticker):
    for data_ticker in buy_list.find({"_id":ticker}):
        stock  = data_ticker["_id"]
        bing = bing_search(stock)
        for get_bing in bing:
            if ticker == get_bing['ticker']:
                try:
                    buy_list.update_one(
                        # fix upsert 

                        {'_id': get_bing['ticker']},
                        {'$push': {'bing_news': get_bing}},
                        #upsert must be True or False

                        
                        # {'$set': {'bing_news': get_bing}},

                    )
                except Exception as e:
                    print(e)
                    pass
        text_append, internal_id, stories_title, stories_link, article_day_published  = bloomberg_current(stock)
        bloomberg_current_data = {
                        'internal_id': internal_id,
                        'title': stories_title,
                        'link': stories_link,
                        'date': article_day_published,
                        'text': text_append
                    }
        print(bloomberg_current_data)
        try:
            buy_list.update_one(
                {'_id': stock},
                {'$push': {'bloomberg_news':bloomberg_current_data}},
            
            )
        except Exception as e:
            print(e)
            pass
        # if ticker == get_bing['ticker']:
        #     text_append, internal_id, stories_title, stories_link, article_day_published = bloomberg_current(ticker = stock)
            



# check_buying_list()

def routine_update(ticker):
    for data_ticker in buy_list.find({"_id":ticker}):
        stock  = data_ticker["_id"]
        bing = bing_search(stock)
        bloomberg_cdn = bloomberg_current(ticker = stock)
        for get_bing in bing:
            if ticker == get_bing['ticker']:
                try:
                    buy_list.update_one(
                        {'_id': get_bing['ticker']},
                        {'$push': {'bing_news': get_bing}},
                        {'$push': {'bloomberg_news': bloomberg_cdn}}
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
