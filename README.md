# Amazon-Price-Check

A Pricer checker for mainly amazon which notifies you via email about a new alltime price low.
It also creates a semicolon seperated history file with the price, date, time and article description.

The standart poll interval is set to 1h. If the endless flag is not set a random time between 1 - 10 minutes will be waited for a poll.

  -h, --help                                            show this help message and exit
  
  -c CONFIG, --config CONFIG                            Configuration file path
  
  -t POLL_INTERVAL, --poll-interval POLL_INTERVAL       Time in seconds between checks
  
  -o OUTPUTFILE, --outputfile OUTPUTFILE                History filename for history data, default =price_history.txt
  
  -e, --endless                                         Endless Run
