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
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

glob_message_all_time_low = ''
glob_message_changed = ''
glob_message_title = ''
glob_debug = False

def send_email(price, url, article, email_credentials, new_alltime_low_bool=False):
    if glob_debug:
        print("Completely skipping email creation")
        return
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
        msg['To'] = email_credentials['receiver']
        if (new_alltime_low_bool):
            text = glob_message_all_time_low % (article, price, url)
        else:
            text = glob_message_changed % (article, price, url)
        part = MIMEText(text, 'plain', _charset='utf-8')
        msg.attach(part)
        try:
            s.sendmail(str(email_credentials['user']), str(email_credentials['user']), msg.as_string())
            print('Message has been sent.')
            s.quit()
        except Exception as e:
            print("Failed to send email!")
            print(e)
            s.quit()

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config',default='%s/config.json' % os.path.dirname(os.path.realpath(__file__)), help='Configuration file')
    parser.add_argument('-p', '--poll-interval', type=int, default=3600, help='Time in seconds between checks, default 1 hour')
    parser.add_argument('-r', '--random-poll', type=int, default=0, help='Random wait time between 0 and input to add to poll-interval')
    parser.add_argument('-e', '--endless', action='store_true', help='Endless Run')
    parser.add_argument('-d', '--dump-html', action='store_true', help='Stores all html files in /html-dump')
    parser.add_argument('-x', '--debug', action='store_true', help='Sets debug flag. Will not send email and produce extended output')
    return parser.parse_args()

def read_config(config_file):
    if glob_debug:
        print("Reading Config File...")
    try:
        with open(config_file, 'r') as f:
            return json.loads(f.read())
    except Exception as e:
        print('Failed to open config file')
        print(e)
        exit()

def write_config(config_file, data):
    try:
        with open(config_file, 'w') as f:
            json.dump(data, f, indent=4, sort_keys=True)
    except Exception as e:
        print('Failed to write config file!')
        print(e)

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

def update_items(items, email_credentials, html_dump):
    prices_updated = False
    for item in items:
        if glob_debug:
            print("Processing items...")
        current_regex = item['regex']
        current_listid = item['listid']
        current_items = item['item']
        current_historyfile = item['historyfile']
        notify_on_every_change = item['notify_on_every_change']

        for each_item in current_items:
            if glob_debug:
                print("Processing item", each_item[3])
            item_url = each_item[0]
            last_price = each_item[1]
            all_time_low_price = each_item[2]
            item_name = each_item[3]


            print('\nChecking', item_name)
            current_price = get_price(item_url, current_regex, current_listid, html_dump, item_name)
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
            wait(90, 23) #wait between polling items
    return prices_updated

def create_folder(foldername):
    try:
        if not os.path.exists(foldername):
            os.makedirs(foldername)
    except OSError:
        print("Cannot create folders")
        exit()

def get_random_header():
    header_list = list()

    #Chrome
    current_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'}
    header_list.append(current_dict)

    #IE
    current_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; rv:11.0) like Gecko'}
    header_list.append(current_dict)

    #Firefox
    current_dict = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1'}
    header_list.append(current_dict)

    rand = randint(1,20)
    if rand <= 14:
        if glob_debug:
            print("Using header Chrome\n", header_list[0])
        return header_list[0]
    elif rand > 14 and rand <= 18:
        if glob_debug:
            print("Using header Firefox\n", header_list[2])
        return header_list[2]
    else:
        if glob_debug:
            print("Using header IE\n", header_list[1])
        return header_list[1]

def get_price(URL, regex, regex_price_id, html_dump, item_name):
    #Get Wegpage content
    r = requests.get(URL, headers=get_random_header())
    #Raises Excpetion if occured
    try:
        r.raise_for_status()
    except Exception as e:
        print(e)
        return 0
    htmlfile = r.text

    if glob_debug:
        length = len(htmlfile)
        unit = "bytes"
        if length >= 1024:
            length = round(length / 1024)
            unit = "kBytes"
            if length >= 1024:
                length = round(length / 1024)
                unit = "MBytes"
        print("Fetched URL, got", length, unit)

    if html_dump:
        create_folder("html-dump")

        if glob_debug:
            print("Dumping html for", item_name)

        time_stamp = time.time()
        filepath = "html-dump/" + item_name + " - " + str(time_stamp) + ".html"

        if glob_debug:
            print("File(path) set to:", filepath)

        with open(filepath, mode='w', encoding='utf-8') as f:
            f.write(htmlfile)

    if glob_debug:
        print("Read in regex from config is:\n", regex)

    price_string = re.findall(regex, htmlfile)

    if glob_debug:
        print("Extracted price string:", price_string)
        print("With type:", type(price_string))

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
        except Exception as e:
            print("ERROR: Cannot find price string")
            print("Price String was:", price)
            print(e)
            return 0

def write_history(history_file, price, itemname):
    current_date = time.strftime("%d/%m/%Y")
    current_time = time.strftime("%H:%M:%S")

    with open(history_file, 'a') as history:
        history.write("%s;%s;%s;%s\n" % (current_date, current_time, price, itemname))

def main():
    args = parse_arguments()
    global glob_debug

    glob_debug = args.debug

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
            if(update_items(config['items'], config['email'], args.dump_html)):
                write_config(args.config, config)
            sys.stdout.flush()
            wait(args.random_poll, args.poll_interval)
    else:
        if(update_items(config['items'], config['email'], args.dump_html)):
            write_config(args.config, config)

if __name__ == '__main__':
	main()
