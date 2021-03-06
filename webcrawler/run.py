#!/usr/bin/env python3

import csv

from unittest.mock import sentinel

from msnbc import MsnbcCrawler
from fox import FoxCrawler


def scrape(crawler, outfile, max_iter):
    print("...0%", end="\r")
    with open(outfile, 'w', newline='') as f:
        csvw = csv.writer(f, quoting=csv.QUOTE_ALL) 
        csvw.writerow( ('speaker', 'text') )
        count = 0
        gen = crawler.get_cleaned_text()
        text = next(gen, sentinel.THE_END)
        while count < max_iter and not text == sentinel.THE_END:
            csvw.writerows(text)
            print("...%s%%" % int((count / max_iter) * 100), end="\r")
            count = count + 1
            text = next(gen, sentinel.THE_END)

    if count == max_iter:
        print("Stopped by MAX_ITER")
    else:
        print("Stopped by empty transcript list")
    print("Scraped %s transcripts successfully" % count)


if __name__ == "__main__":
    print("Scraping Sean...")
    scrape(FoxCrawler(), 'out/hannity.csv', 1000)

    print("Scraping Maddow...")
    scrape(MsnbcCrawler(), 'out/maddow.csv', 700)