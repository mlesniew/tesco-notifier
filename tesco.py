#!/usr/bin/env python3

from datetime import datetime, date, timedelta
import argparse
import pickle
import random
import re
import time

import requests


def login(username, password):
    print('Logging in...')
    session = requests.Session()

    session.get('https://ezakupy.tesco.pl/groceries/pl-PL/')
    resp = session.get('https://ezakupy.tesco.pl/groceries/pl-PL/login',
                       params={'from': 'https://ezakupy.tesco.pl/groceries/pl-PL/'})

    match = re.search('data-csrf-token="([^"]+)"', resp.text)
    csrf_token = match.group(1)

    resp = session.post('https://ezakupy.tesco.pl/groceries/pl-PL/login',
                 params={'from': 'https://ezakupy.tesco.pl/groceries/pl-PL/'},
                 data={
                     'email': username,
                     'password': password,
                     'onSuccessUrl': 'https://ezakupy.tesco.pl/groceries/pl-PL/',
                     '_csrf': csrf_token
                     })
    assert resp.ok

    print('Logged in.')
    session.hooks = {
            'response': lambda r, *args, **kwargs: r.raise_for_status()
            }
    return session


def load_last_found(filename):
    print('Loading cache...')
    try:
        with open(filename, 'br') as f:
            ret = pickle.load(f)
        print('Loaded last available:')
        for slot in sorted(ret):
            print(' * %s' % slot)
        return ret
    except Exception as e:
        print('Error loading last available: %s' % e)
        return set()


def save_last_found(filename, data):
    print('Storing cache...')
    with open(filename, 'wb') as f:
        pickle.dump(data, f)


def iter_available(session, weeks=3):
    resp = session.get('https://ezakupy.tesco.pl/groceries/pl-PL/slots/delivery')
    assert resp.ok

    day = date.today()

    for _ in range(weeks):
        print('Checking available slots in the week of %s' % day)
        resp = session.get('https://ezakupy.tesco.pl/groceries/pl-PL/slots/delivery/%s' % day,
                params={'slotGroup': 2}, headers={'accept': 'application/json'})
        assert resp.ok

        slots = resp.json()['slots']
        for slot in slots:
            if slot.get('status') != 'UnAvailable':
                yield slot['start']

        day += timedelta(7)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--username', '-u', required=True)
    parser.add_argument('--password', '-p', required=True)
    parser.add_argument('--cache', '-c', default='tesco.dat')
    parser.add_argument('--token', '-t', action='append',
                        help='WirePusher.com token')
    parser.add_argument('--interval', '-i', default=0, type=int)

    args = parser.parse_args()
    print(args)

    last_available = load_last_found(args.cache)
    store_cache = False

    try:
        while True:
            session = login(args.username, args.password)

            try:
                while True:
                    available = set(iter_available(session))
                    store_cache = store_cache or (available != last_available)

                    print('%i slot(s) found.' % len(available))
                    for slot in sorted(available):
                        new = slot not in last_available
                        print('* %s%s' % (slot, ' (new)' if new else ''))

                    new_available = available - last_available
                    if new_available and args.token:
                        if len(new_available) == 1:
                            text = 'Nowy termin dostawy w Tesco: %s' % new_available[0]
                        else:
                            first, last = min(new_available), max(new_available)
                            text = 'Nowe terminy dostawy w Tesco (%i), pierwszy %s, ostatni %s' % (len(new_available), first, last)

                        requests.get('https://wirepusher.com/send',
                                     params={
                                         'id': ','.join(args.token),
                                         'title': 'Tesco',
                                         'message': text,
                                         'type': 'tesco'
                                    })

                    last_available = available

                    if args.interval <= 0:
                        break
                    else:
                        print('Sleeping...')
                        time.sleep(random.random() * args.interval)
            except Exception as e:
                print('Exception %s' % e)
                # who cares

            if args.interval <= 0:
                break
            else:
                print('Sleeping...')
                time.sleep(random.random() * args.interval)

    finally:
        if store_cache:
            save_last_found(args.cache, last_available)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        raise SystemExit('Abort.')
