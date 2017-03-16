#!/usr/bin/python

import os
import re
import json
import time
import requests
import smtplib
import argparse
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
    except Exception:
        print('Someting Wong')
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


def get_price(url, regex, listid):
    #Get Wegpage content
    r = requests.get(url, headers={
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36'
    })
    #Raises Excpetion if occured
    r.raise_for_status()
    htmlfile = r.text

    price_string = re.findall(regex, htmlfile)
    try:
        if not type(listid) is int:
            raise TypeError
        else:
            if listid < 0:
                raise ValueError
    except TypeError:
        print('ListID is not of type Integer')
        return 0
    except ValueError:
        print('ListID must be >= 0')
        return 0
    except Exception:
        print('Unhandled error with ListID')
        return 0

    try:
        price_string = price_string[0][listid]
        price = float(price_string.replace(',', '.'))
        return price
    except Exception:
        print("ERROR: Cannot find price string")
        return 0


def get_config(config):
    with open(config, 'r') as f:
        return json.loads(f.read())


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',default='%s/config.json' % os.path.dirname(os.path.realpath(__file__)), help='Configuration file path')
    parser.add_argument('-t', '--poll-interval', type=int, default=3600, help='Time in seconds between checks, default 1 hour')
    parser.add_argument('-r', '--random-poll', action='store_true', help='Adds 1 to 10 min to poll intervall randomly')
    parser.add_argument('-o', '--outputfile', default='%s/price_history.txt' % os.path.dirname(os.path.realpath(__file__)), help='History filename for history data, default = price_history.txt')
    parser.add_argument('-e', '--endless', action='store_true', help='Endless Run')
    return parser.parse_args()

def write_config(config, data):
    with open(config, 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)

def compare_prices(items, config, history_file):
    prices_updated = False

    for item in copy(items):
        print('Checking price for %s (should be lower than %s)' % (item[2], item[1]))
        item_page = item[0]
        price = get_price(item_page, config['regex'], config['listid'])

        if(history_file != "NONE"):
            price_file = open(history_file, 'a')
            price_file.write("%s;%s;%s;%s\n" % (time.strftime("%d/%m/%Y"), time.strftime("%H:%M:%S"), price, str(item[2])))

        if not price:
            continue
        elif price < item[1]:
            print('Price is %s!! Trying to send email.' % price)
            send_email(price, item_page, config['email'], item[2])
            print('Updating config for new price!')
            item[1] = price
            prices_updated = True
        else:
            print('Price is %s. Ignoring...' % price)

        if(history_file != "NONE"):
            price_file.close()
    return prices_updated

def wait(poll_interval, random=False):
    if random:
        random_number = randint(60,600)
        random_number += poll_interval
    else:
        random_number = poll_interval
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
            wait(args.poll_interval, args.random_poll)
    else:
        if compare_prices(items, config, args.outputfile):
            write_config(args.config, config)

    print('Run completed, exiting')


if __name__ == '__main__':
	#Necessary because started with system.d. Otherwise crash because of no available ethernet
	#time.sleep(10)
	main()
