# Amazon-Price-Check

A Pricer checker for mainly amazon which notifies you via email about a new all time price low.
It also creates a semicolon seperated history file with the price, date, time and article description.

The regular expression that gets the item price must be inserted into the json file. Example for amazon included.
The List id specifies where to find the price in the list returned by regex.findall.

The standart poll interval is set to 1h. If the endless flag is not set a random time between 1 - 10 minutes will be waited for a poll.

  -h, --help                                            show this help message and exit
  
  -c CONFIG, --config CONFIG                            Configuration file
  
  -t POLL_INTERVAL, --poll-interval POLL_INTERVAL       Time in seconds between checks
  
  -o OUTPUTFILE, --outputfile OUTPUTFILE                History filename for history data, default =price_history.txt
														if -o NONE no history will be created
  
  -e, --endless                                         Endless Run
