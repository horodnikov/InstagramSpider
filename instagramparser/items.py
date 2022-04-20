# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import scrapy


class InstagramparserItem(scrapy.Item):
    # define the fields for your item here like:
    _id = scrapy.Field()
    user_id = scrapy.Field()
    username = scrapy.Field()
    follower_data = scrapy.Field()
    follower_id = scrapy.Field()
    following_data = scrapy.Field()
    following_id = scrapy.Field()
    post_data = scrapy.Field()
    post_id = scrapy.Field()