from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from instagramparser.spiders.Instagram import InstagramSpider
from instagramparser import settings
from pymongo import MongoClient

MONGO_HOST = 'localhost'
MONGO_PORT = 27017
DB_NAME = 'Instagram'


def search_data(user, data):
    with MongoClient(host=MONGO_HOST, port=MONGO_PORT) as client:
        db = client[DB_NAME]
        search_filter = {"$and": [{data: {"$exists": True}}, {'username': user}]}
        count_items = db['Instagram'].count_documents(search_filter)
        posts_list = [item[data] for item in db['Instagram'].find(search_filter)]
        print(f"Count user's {data.replace('_data', '')}s: {count_items}\n")
    return posts_list


if __name__ == '__main__':

    crawler_settings = Settings()
    crawler_settings.setmodule(settings)

    users_to_scrape = input(
        'Type users to scrape (via space separator): ').split()
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(InstagramSpider, users_to_scrape=users_to_scrape)
    process.start()

    user_name = 'ai.machine_learning'
    posts = search_data(user=user_name, data='post_data')
    following = search_data(user=user_name, data='following_data')
    follower = search_data(user=user_name, data='follower_data')
