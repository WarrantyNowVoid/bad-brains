from bs4 import BeautifulSoup
import requests

from crawler import TranscriptCrawler

BASEURL = "http://www.msnbc.com"
TRANSCRIPT_PATH = "/transcripts/rachel-maddow-show/"
MONTH_TEMPLATE = "%(baseurl)s/%(path)s/%(year)s/%(month)s"

START_MONTH = 7
START_YEAR = 2020
END_MONTH = 9
END_YEAR = 2008


class MsnbcCrawler(TranscriptCrawler):

    def __init__(self):
        super().__init__()
        
        self.month = START_MONTH
        self.year = START_YEAR

        self.clean_patterns = [
            r'^Show: .*',
            r'^Date: .*',
            r'^Guest: .*',
            r'^THIS IS A RUSH TRANSCRIPT.*',
            r'^BE UPDATED.*',
            r'^END$',
            r'^Copyright [0-9]+ .*',
            r'^protected by United States copyright.*',
            r'^United States copyright law.*',
            r'^distributed, transmitted, displayed.*',
            r'^transmitted, displayed, published.*',
            r'^Content and programming copyright.*',
            r'^prior written permission.*',
            r'^or remove any trademark.*',
            r'^copyright or other notice.*',
            r'^content\.>$'
        ]
        self.transcript_graf_selector = 'div.content div.pane-node-body div.field-name-body p'

    def fetch_post_batch(self):
        batch_content = []

        if self.year == END_YEAR and self.month == END_MONTH - 1:
            return batch_content

        params = {
            'baseurl': BASEURL,
            'path': TRANSCRIPT_PATH,
            'month': self.month,
            'year': self.year
        }
        url = MONTH_TEMPLATE % params

        res = requests.get(url)
        if res.status_code == 200:
            post_list = []
            soup = BeautifulSoup(res.text, 'html.parser')
            for link in soup.select('div.pane-msnbc-transcript-index div.transcript-item a'):
                post_list.append(BASEURL + link.get('href'))

            self.month = self.month - 1
            if self.month == 0:
                self.month = 12
                self.year = self.year - 1
        else:
            raise RuntimeError("Couldn't fetch an article batch (month %s, year %s) %s: %s" % (self.month, self.year, res.status_code, res.text))

        for post_url in post_list:
            resp = requests.get(post_url)
            if resp.status_code == 200:
                batch_content.append(self.clean_text(resp.text))
            else:
                raise RuntimeError("Couldn't fetch an article (%s) %s: %s" % (post_url, resp.status_code, resp.text))

        return batch_content