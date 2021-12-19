import toml
from pathlib import Path
from extendBrokers.utilities import load_config

def get_news_urls():
    links = load_config().news_source
    print(links)
    # return links

    # return links

    # print(links)

# NEWS_URL = "https://newsapi.org/v2/top-headlines?sources={}&apiKey={}"