#!/usr/bin/env python

from bs4 import BeautifulSoup
from urllib2 import urlopen
from datetime import datetime
import csv
import sys
import os
import smtplib
import config

# Craigslist search URL
SEARCH_URL = ('http://minneapolis.craigslist.org/search/sss?query={0}')
BASE_URL = "http://minneapolis.craigslist.org"

class Result:
    """ Creates object from passed in HTML. Should be one row element from base search"""
    def __init__(self, row):
        self.url = BASE_URL + row.find("a", "result-title")['href']
        if row.find("span", "result-price"):
            self.price = row.find("span", "result-price").get_text()
        else:
            self.price = "NA"
        self.create_date = row.find('time').get('datetime')
        self.title = row.find('a', 'result-title').get_text()

    def print_out(self):
        print "Title: " + self.title
        print "Price: " + self.price
        print "Creation Date: " + self.create_date
        print "URL: " + self.url
        print


def parse_results(search_term):
    results = []
    search_term = search_term.strip().replace(' ', '+')
    search_url = SEARCH_URL.format(search_term)
    soup = BeautifulSoup(urlopen(search_url).read())
    rows = soup.find_all("li", "result-row")
    for row in rows:
        formattedResult = Result(row)
        results.append(formattedResult)
    return results

def record_results(results):
    """ Writes URLs to file so we can keep track of what posts have been seen """
    with open('results.csv', 'w') as f:
        for x in results:
            f.write(x.url)
            f.write("\n")

def has_new_records(results):
    current_posts = [x.url for x in results]
    fields = ["url"]
    if not os.path.exists('results.csv'):
        return True

    with open('results.csv', 'r') as f:
        reader = csv.DictReader(f, fieldnames=fields, delimiter='|')
        seen_posts = [row['url'] for row in reader]

    is_new = False
    for post in current_posts:
        if post in seen_posts:
            pass
        else:
            is_new = True
    return is_new

def send_text(phone_number, msg):
    fromaddr = "Craigslist Checker"
    toaddrs = phone_number + "@tmomail.net"
    msg = ("From:{0}\r\nTo:{1}\r\nSubject:New Craigslist Result\r\n\r\n{2}").format(fromaddr, toaddrs, msg)
    server = smtplib.SMTP('smtp.gmail.com:587')
    server.starttls()
    server.login(config.data['username'], config.data['password'])
    server.sendmail(fromaddr, toaddrs, msg)
    server.quit()

def get_current_time():
    return datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')

if __name__ == '__main__':
    try:
        SEARCH_TERM = sys.argv[1]
        PHONE_NUMBER = config.data['phone']
    except:
        print "You need to include a search term and a 10-digit phone number!\n"
        sys.exit(1)

    if len(PHONE_NUMBER) != 10:
        print "Phone numbers must be 10 digits!\n"
        sys.exit(1)

    results = parse_results(SEARCH_TERM)

    # Send an SMS message if there are new results. Only send first result to avoid spamming texts.
    if has_new_records(results):
        message = "Title: {0}\nPrice: {1}\nURL: {2}".format(results[0].title, results[0].price, results[0].url)
        print "[{0}] There are new results - sending text message to {1}".format(get_current_time(), PHONE_NUMBER)
        send_text(PHONE_NUMBER, message)
        record_results(results)
    else:
        print "[{0}] No new results - will try again later".format(get_current_time())

