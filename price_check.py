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

glob_message_all_time_low = ''
glob_message_changed = ''
glob_message_title = ''

def send_email(price, url, article, email_credentials, new_alltime_low_bool=False):
    try:
        s = smtplib.SMTP_SSL(email_credentials['smtp_url'])
        s.login(str(email_credentials['user']), str(email_credentials['password']))
    except smtplib.SMTPAuthenticationError:
        print('Failed to login')
    except smtplib.SMTPConnectError:
        print('Failed to connect to SMTP server')
    except Exception:
        print('Someting Wong with Email sending')
    else:
        print('Logged in! Composing message..')
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '%s Price Alert - %s' % (article, price)
        msg['From'] = email_credentials['user']
        msg['To'] = email_credentials['user']
        if (new_alltime_low_bool):
            text = glob_message_all_time_low % (article, price, url)
        else:
            text = glob_message_changed % (article, price, url)
        part = MIMEText(text, 'plain')
        msg.attach(part)
        s.sendmail(str(email_credentials['user']), str(email_credentials['user']), msg.as_string())
        print('Message has been sent.')

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',default='%s/config.json' % os.path.dirname(os.path.realpath(__file__)), help='Configuration file')
    parser.add_argument('-p', '--poll-interval', type=int, default=3600, help='Time in seconds between checks, default 1 hour')
    parser.add_argument('-r', '--random-poll', type=int, default=0, help='Random wait time between 0 and input to add to poll-interval')
    parser.add_argument('-e', '--endless', action='store_true', help='Endless Run')
    return parser.parse_args()

def read_config(config_file):
    try:
        with open(config_file, 'r') as f:
            return json.loads(f.read())
    except Exception:
        print('Failed to open config file')
        exit()

def write_config(config_file, data):
    try:
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)
    except Exception:
        print('failed to write config file!')

def wait(random, waittime):
    #No unsigned datatype, so just convert any negative to positive
    if(random < 0):
        random *= -1
        print('Negative random wait time given, convert to positive')
    if(waittime < 0):
        waittime *= -1
        print('Negative wait time given, convert to positive')

    random_wait_time = randint(0,random)
    random_wait_time += waittime
    print('Sleeping for', random_wait_time, 'seconds')
    time.sleep(random_wait_time)

def update_items(items, email_credentials):
    prices_updated = False
    for item in items:
        current_regex = item['regex']
        current_listid = item['listid']
        current_items = item['item']
        current_historyfile = item['historyfile']
        notify_on_every_change = item['notify_on_every_change']

        for each_item in current_items:
            item_url = each_item[0]
            last_price = each_item[1]
            all_time_low_price = each_item[2]
            item_name = each_item[3]


            print('\nChecking', item_name)
            current_price = get_price(item_url, current_regex, current_listid)
            if (current_price < all_time_low_price):
                print('New price is', current_price, '!!')
                all_time_low_price = current_price
                last_price = current_price
                prices_updated = True
                send_email(current_price, item_url, item_name, email_credentials, True)
            elif(current_price != last_price):
                print('Price has changed, it\'s now:', current_price)
                last_price = current_price
                prices_updated = True
                if(notify_on_every_change):
                    send_email(current_price, item_url, item_name, email_credentials)
            else:
                print('Price is at %.2f hasn\'t changed...' % current_price)
            if(current_historyfile != 'NONE'):
                write_history(current_historyfile, current_price, each_item[2])
            else:
                print('No history file requested, omitting...')

            if (prices_updated == True):
                each_item[1] = last_price
                each_item[2] = all_time_low_price
    return prices_updated


def get_price(URL, regex, regex_price_id):
    #Get Wegpage content
    r = requests.get(URL, headers={
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
            '(KHTML, like Gecko) Chrome/52.0.2743.82 Safari/537.36'
    })
    #Raises Excpetion if occured
    r.raise_for_status()
    htmlfile = r.text

    price_string = re.findall(regex, htmlfile)

    try:
        if not type(regex_price_id) is int:
            raise TypeError
        else:
            if regex_price_id < 0:
                raise ValueError
    except TypeError:
        print('regex_price_id is not of type Integer')
        return 0
    except ValueError:
        print('regex_price_id must be >= 0')
        return 0
    except Exception:
        print('Unhandled error with regex_price_id')
        return 0

    #If Object is just a list
    try:
        price = price_string[regex_price_id]
        price = float(price.replace(',', '.'))
        return price
    except Exception:
        #If object is a tuple in a list. Thats the case when re.findall() returns multiple results
        try:
            price = price_string[0][regex_price_id]
            price = float(price.replace(',', '.'))
            return price
        except Exception:
            print("ERROR: Cannot find price string")
            return 0

def write_history(history_file, price, itemname):
    current_date = time.strftime("%d/%m/%Y")
    current_time = time.strftime("%H:%M:%S")

    with open(history_file, 'a') as history:
        history.write("%s;%s;%s;%s\n" % (current_date, current_time, price, itemname))

def main():
    args = parse_arguments()
    config = read_config(args.config)
    global glob_message_changed
    global glob_message_all_time_low
    global glob_message_title

    try:
        glob_message_all_time_low = config['email']['message_all_time_low']
        if(glob_message_all_time_low.count("%s") != 3):
            print('Amount of reguired place holders \"%s\" is not 3!\n')
            raise Exception()
    except Exception:
        print('Failed to set message for all time low!\n')
        glob_message_all_time_low = '%s price has a new all time low!\nThe price is currently %s !! URL to salepage: %s'

    try:
        glob_message_changed = config['email']['message_changed']
        if(glob_message_changed.count("%s") != 3):
            print('Amount of reguired place holders \"%s\" is not 3! Falling back to standard')
            raise Exception()
    except Exception:
        print('Failed to set message for price change! Using standard')
        glob_message_changed = '%s price has changed\nThe price is currently %s !! URL to salepage: %s'

    try:
        glob_message_title = config['email']['message_title']
        if(glob_message_title.count("%s") != 2):
            print('Amount of reguired place holders \"%s\" is not 2! Falling back to standard')
            raise Exception()
    except Exception:
        print('Failed to set message title! Using standard')
        glob_message_title = '%s Price Alert - %s'

    if args.endless:
        while(True):
            if(update_items(config['items'], config['email'])):
                write_config(args.config, config)
            wait(args.random_poll, args.poll_interval)
    else:
        if(update_items(config['items'], config['email'])):
            write_config(args.config, config)

if __name__ == '__main__':
	main()
