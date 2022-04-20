# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from pymongo import MongoClient
import timestring


MONGO_HOST = 'localhost'
MONGO_PORT = 27017
DB_NAME = 'Instagram'


class InstagramparserPipeline:
    def __init__(self):
        self.client = MongoClient(host=MONGO_HOST, port=MONGO_PORT)
        self.db = self.client[DB_NAME]

    def process_item(self, item, spider):
        post = item.get("post_data", None)
        follower = item.get("follower_data", None)
        following = item.get("following_data", None)

        if post:
            item["post_data"]["date"] = self.str_to_date(post["date"])
            self.db.get_collection(spider.name).update_one(
                {'post_id': item['post_id']}, {"$set": item},
                upsert=True)

        elif follower:
            self.db.get_collection(spider.name).update_one(
                {'follower_id': item['follower_id']}, {"$set": item},
                upsert=True)

        elif following:
            self.db.get_collection(spider.name).update_one(
                {'following_id': item['following_id']}, {"$set": item},
                upsert=True)

        return item

    @staticmethod
    def str_to_date(date_string):
        try:
            if date_string:
                return timestring.Date(f'{date_string}').date
        except timestring.TimestringInvalid:
            pass
