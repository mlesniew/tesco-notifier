# Tesco Notifier

Notifies about new home delivery time slots on [ezakupy.tesco.pl](https://ezakupy.tesco.pl) as they become available.

## Requirements

All that's needed to run this is the [requests module](https://github.com/psf/requests) this is the requests module and optionally the [Wirepusher app](http://wirepusher.com/) to retrieve notifications.

## Usage

```
usage: tesco.py [-h] --username USERNAME --password PASSWORD [--cache CACHE]
                [--token TOKEN] [--interval INTERVAL]

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME, -u USERNAME
  --password PASSWORD, -p PASSWORD
  --cache CACHE, -c CACHE
  --token TOKEN, -t TOKEN
                        WirePusher.com token
  --interval INTERVAL, -i INTERVAL
```
