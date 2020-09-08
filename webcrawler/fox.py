import json
import urllib.parse

import requests

from crawler import TranscriptCrawler

BASEURL = "https://www.foxnews.com"
API_SEARCH_CATEGORY = "fox-news/shows/hannity/transcript"
API_URL_TEMPLATE = "%(baseurl)s/api/article-search?isCategory=false&isTag=true&isKeyword=false&isFixed=false&isFeedUrl=false&searchSelected=%(category)s&contentTypes=%%7B%%22interactive%%22:false,%%22slideshow%%22:false,%%22video%%22:false,%%22article%%22:true%%7D&size=%(count)s&offset=%(offset)s"


class FoxCrawler(TranscriptCrawler):

    def __init__(self):
        super().__init__()

        self.offset = 0
        self.count = 10

        self.clean_patterns = [
            r'^This is a rush transcript.*'
        ]
        self.transcript_graf_selector = '.article-body p'

    def fetch_post_batch(self):
        batch_content = []

        params = {
            'baseurl': BASEURL,
            'category': urllib.parse.quote(API_SEARCH_CATEGORY, safe=""),
            'count': self.count,
            'offset': self.offset
        }
        url = API_URL_TEMPLATE % params

        res = requests.get(url)
        if res.status_code == 200:
            post_list = json.loads(res.text)
            self.offset = self.offset + self.count
        else:
            raise RuntimeError("Couldn't fetch an article batch (count %s, offset %s) %s: %s" % (self.count, self.offset, res.status_code, res.text))

        for post in post_list:
            post_cat = post['category']['name']
            if post_cat in ["TRANSCRIPT"]:
                post_url = BASEURL + post['url']

                resp = requests.get(post_url)
                if resp.status_code == 200:
                    batch_content.append(self.clean_text(resp.text))
                else:
                    raise RuntimeError("Couldn't fetch an article (%s) %s: %s" % (post_url, resp.status_code, resp.text))

        return batch_content