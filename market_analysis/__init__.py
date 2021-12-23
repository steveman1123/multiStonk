# this file is used to save to database:
# from pymongo import MongoClient, collation, collection, cursor, database
# import datetime

# # my_srv = "mongodb://127.0.0.1:27017/?readPreference=primary&serverSelectionTimeoutMS=2000&appname=MongoDB%20Compass&directConnection=true&ssl=false"

# def database_(my_srv):
    
#     client = MongoClient(my_srv)
#     todays_date = datetime.datetime.now().strftime("%Y_%m_%d")
#     NEWS_DATABASE  = client.Caduceus_
#     NEWS_COLLECTION = NEWS_DATABASE.Caduceus_[todays_date]
#     BING_NEWS = NEWS_COLLECTION.bing_headlines
#     BLOOMBERG_CDN = NEWS_COLLECTION.bloomberg_cdn
#     # db = client.get_database("Caduceus_" + todays_date)
#     # return NEWS_DATABASE
