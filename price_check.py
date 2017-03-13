#!/usr/bin/python

import os
import re
import json
import time
import requests
import smtplib
import argparse
import urlparse
import sys
import time
from random import randint
from copy import copy
from lxml import html
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(price, url, email_info, article):
    try:
        s = smtplib.SMTP_SSL(email_info['smtp_url'])
        #s.starttls()
        s.login(str(email_info['user']), str(email_info['password']))
    except smtplib.SMTPAuthenticationError:
        print('Failed to login')
    else:
        print('Logged in! Composing message..')
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Price Alert - %s' % price
        msg['From'] = email_info['user']
        msg['To'] = email_info['user']
        text = '%s price has a new all time low!\nThe price is currently %s !! URL to salepage: %s' % (
            article, price, url)
        part = MIMEText(text, 'plain')
        msg.attach(part)
        s.sendmail(str(email_info['user']), str(email_info['user']), msg.as_string())
        print('Message has been sent.')


def get_price(url, selector):
    #Get Wegpage content
    r = requests.get(url, headers={
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36'
    })
    #Raises Excpetion if occured
    r.raise_for_status()
    htmlfile = r.text
    price_string = re.findall('(<span id="priceblock_(our|deal)price" class="a-size-medium a-color-price">)(\w+\s\d+(,|\.)\d+)', htmlfile)
    try:
        match = False
        while not match:
            for i in price_string[0]:
                if (i.find("EUR") != -1):
                    match = True
                    price_string = re.findall('(\d+(,|\.)\d+)', i)[0][0]
    except Exception:
        print("Cannot find price string")
    price = float(price_string.replace(',', '.'))
    return price


def get_config(config):
    with open(config, 'r') as f:
        return json.loads(f.read())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',
                        default='%s/config.json' % os.path.dirname(
                            os.path.realpath(__file__)),
                        help='Configuration file path')
    parser.add_argument('-t', '--poll-interval', type=int, default=3600,
                        help='Time in seconds between checks')
    parser.add_argument('-o', '--outputfile', default='%s/price_history.txt' % os.path.dirname(os.path.realpath(__file__)), help='History filename for history data, default = price_history.txt')
    parser.add_argument('-e', '--endless', action='store_true', help='Endless Run')
    return parser.parse_args()

def write_config(config, data):
    with open(config, 'w') as f:
        json.dump(data, f)

def compare_prices(items, config, history_file):
    prices_updated = False

    for item in copy(items):
        print('Checking price for %s (should be lower than %s)' % (item[2], item[1]))
        item_page = urlparse.urljoin(config['base_url'], item[0])
        price = get_price(item_page, config['xpath_selector'])
        price_file = open(history_file, 'a')

        price_file.write("%s;%s;%s;%s\n" % (time.strftime("%d/%m/%Y"), time.strftime("%H:%M:%S"), price, str(item[2])))
        if not price:
            continue
        elif price < item[1]:
            price_file.close()
            print('Price is %s!! Trying to send email.' % price)
            send_email(price, item_page, config['email'], item[2])
            print('Updating config for new price!')
            item[1] = price
            prices_updated = True
        else:
            print('Price is %s. Ignoring...' % price)
            price_file.close()
    if prices_updated:
        return True
    else:
        return False

def wait(poll_interval, endless):
    random_number = randint(60,600)
    if endless:
        random_number += poll_interval
    print('Sleeping for %d seconds' % random_number)
    time.sleep(random_number)

def main():
    args = parse_args()
    config = get_config(args.config)
    items = config['items']

    if args.endless:
        while True and len(items):
            if compare_prices(items, config, args.outputfile):
                write_config(args.config, config)
            wait(args.poll_interval, args.endless)
    else:
        wait(args.poll_interval, args.endless)
        if compare_prices(items, config, args.outputfile):
            write_config(args.config, config)

    print('Run completed, exiting')


if __name__ == '__main__':
	#Necessary because started with system.d. Otherwise crash because of no available ethernet
	#time.sleep(10)
	main()
