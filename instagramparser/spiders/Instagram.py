import scrapy
from scrapy.http import HtmlResponse
import os
import re
import json
from copy import deepcopy
from urllib.parse import quote
from dotenv import load_dotenv
from instagramparser.items import InstagramparserItem


class InstagramSpider(scrapy.Spider):
    name = 'Instagram'
    allowed_domains = ['instagram.com']
    load_dotenv()

    def __init__(self, users_to_scrape):
        super(InstagramSpider, self).__init__()
        self.start_urls = ['https://instagram.com/']
        self.username = os.getenv("USER_NAME")
        self.enc_password = os.getenv("ENC_PASSWORD")
        self.login_url = "https://www.instagram.com/accounts/login/ajax/"
        self.users_to_scrape = users_to_scrape

        self.graphql_url = "https://www.instagram.com/graphql/query/?"
        self.posts_hash = "396983faee97f4b49ccbe105b4daf7a0"
        self.following_hash = '3dec7e2c57367ef3da3d987d89f9dbc8'
        self.followers_hash = '5aefa9893005572d237da5068082d8d5'

    def parse(self, response: HtmlResponse):
        yield scrapy.FormRequest(
            self.login_url,
            callback=self.user_login,
            method="POST",
            formdata={
                "username": self.username, "enc_password": self.enc_password},
            headers={"X-CSRFToken": self.fetch_csrf_token(response.text)})

    def user_login(self, response: HtmlResponse):
        json_data = response.json()
        if json_data["user"] and json_data["authenticated"]:
            user_id = json_data["userId"]
            print(f"instagram_user_id {user_id}")
            user_to_scrape_urls = [f'/{user_to_scrape}' for user_to_scrape
                                   in self.users_to_scrape]
            for user_to_share, user_to_scrape_url in zip(
                    self.users_to_scrape, user_to_scrape_urls):
                yield response.follow(
                    user_to_scrape_url,
                    callback=self.user_data_parse,
                    cb_kwargs={"username": user_to_share})

    def user_data_parse(self, response: HtmlResponse, username):
        user_id = self.fetch_user_id(response.text, username)
        variables = {"id": user_id, "first": 12}
        str_variables = quote(str(variables).replace("'", '"'))
        post_url = self.graphql_url + \
            f"query_hash={self.posts_hash}&variables={str_variables}"
        following_url = self.graphql_url + \
            f"query_hash={self.following_hash}&variables={str_variables}"
        followers_url = self.graphql_url + \
            f"query_hash={self.followers_hash}&variables={str_variables}"

        yield response.follow(
            post_url,
            callback=self.parse_posts,
            cb_kwargs={
                "username": username,
                "user_id": user_id,
                "variables": deepcopy(variables)})

        yield response.follow(
            following_url,
            callback=self.parse_following,
            cb_kwargs={
                "username": username,
                "user_id": user_id,
                "variables": deepcopy(variables)})

        yield response.follow(
            followers_url,
            callback=self.parse_followers,
            cb_kwargs={
                "username": username,
                "user_id": user_id,
                "variables": deepcopy(variables)})

    def parse_posts(self, response: HtmlResponse, username, user_id, variables):
        data = response.json()
        data = data["data"]["user"]["edge_owner_to_timeline_media"]
        page_info = data.get("page_info", None)
        if page_info["has_next_page"]:
            variables["after"] = page_info["end_cursor"]
            str_variables = quote(str(variables).replace("'", '"'))
            url = self.graphql_url + \
                f"query_hash={self.posts_hash}&variables={str_variables}"
            yield response.follow(
                url,
                callback=self.parse_posts,
                cb_kwargs={
                    "username": username,
                    "user_id": user_id,
                    "variables": deepcopy(variables)})

        posts = data["edges"]
        for post in posts:
            post_data = {}
            tmp = post["node"]
            post_data["photo"] = tmp["display_url"]
            post_data["likes"] = tmp["edge_media_preview_like"]["count"]
            post_data["date"] = tmp["taken_at_timestamp"]
            post_id = tmp["id"]
            yield InstagramparserItem(
                post_data=post_data,
                post_id=post_id,
                user_id=user_id,
                username=username)

    def parse_following(
            self, response: HtmlResponse, username, user_id, variables):
        data = response.json()
        data = data["data"]["user"]["edge_follow"]
        page_info = data.get("page_info", None)
        if page_info["has_next_page"]:
            variables["after"] = page_info["end_cursor"]
            str_variables = quote(str(variables).replace("'", '"'))
            url = self.graphql_url + \
                f"query_hash={self.following_hash}&variables={str_variables}"
            yield response.follow(
                url,
                callback=self.parse_following,
                cb_kwargs={
                    "username": username,
                    "user_id": user_id,
                    "variables": deepcopy(variables)})

        following = data["edges"]
        for following in following:
            following_data = {}
            tmp = following["node"]
            following_data["followed_name"] = tmp["username"]
            following_data["photo"] = tmp["profile_pic_url"]
            following_data["is_private"] = tmp["is_private"]
            following_id = tmp["id"]
            yield InstagramparserItem(
                following_id=following_id,
                following_data=following_data,
                user_id=user_id,
                username=username)

    def parse_followers(
            self, response: HtmlResponse, username, user_id, variables):
        data = response.json()
        data = data["data"]["user"]["edge_followed_by"]
        page_info = data.get("page_info", None)
        if page_info["has_next_page"]:
            variables["after"] = page_info["end_cursor"]
            str_variables = quote(str(variables).replace("'", '"'))
            url = self.graphql_url + \
                f"query_hash={self.followers_hash}&variables={str_variables}"
            yield response.follow(
                url,
                callback=self.parse_followers,
                cb_kwargs={
                    "username": username,
                    "user_id": user_id,
                    "variables": deepcopy(variables)})

        followers = data["edges"]
        for follower in followers:
            follower_data = {}
            tmp = follower["node"]
            follower_data["user_name"] = tmp["username"]
            follower_data["photo"] = tmp["profile_pic_url"]
            follower_data["is_private"] = tmp["is_private"]
            follower_id = tmp["id"]
            yield InstagramparserItem(
                follower_id=follower_id,
                follower_data=follower_data,
                user_id=user_id,
                username=username)

    # Получаем токен для авторизации
    @staticmethod
    def fetch_csrf_token(text):
        matched = re.search('\"csrf_token\":\"\\w+\"', text).group()
        return matched.split(':').pop().replace(r'"', '')

    # Получаем id желаемого пользователя
    @staticmethod
    def fetch_user_id(text, username):
        matched = re.search('{\"id\":\"\\d+\",\"username\":\"\\S+\"}',
                            text).group()
        if username in matched:
            return json.loads(matched).get('id')
