# Amazon-Price-Check

A Price checker for any site. If the price is lower than before you get notified via email.

The regular expression that gets the item price must be inserted into the json file. Example for amazon and alternate.de included.
The List id specifies where to find the price in the list returned by regex.findall().

The Email message text can be specified in the config file. %s will be replace by the variables below:

Json Name:                    MessageText e.g.:                         Amount of %s              %s Order/ Description
message_all_time_low Article  %s reached an all time low of %s\n%s      3                         Article name, New Price, URL to Article
message_changed Article       %s price has changed to %s\n%s            3                         Article name, New Price, URL to Article
message_title                 %s Price Alert - %s                       2                         Article name, New Price

The standart poll interval is set to 1h. If the endless flag is not set a random time between 1 - 10 minutes will be added to the poll-interval.

  -h, --help            								show this help message and exit

  -c CONFIG, --config CONFIG							Configuration file

  -d, --dump-html										Dumps the html in the folder html-dump every time it's been requested.
  
  -p POLL_INTERVAL, --poll-interval POLL_INTERVAL		Time in seconds between checks, default 1 hour

  -r RANDOM_POLL, --random-poll RANDOM_POLL				Random wait time between 0 and input to add to poll-interval

  -e, --endless         								Endless Run
  
  -x, --debug											Shows additional debug information and does not send an email