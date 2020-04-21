#!/usr/bin/env python3

from datetime import datetime, date, timedelta
import json
import pickle
import random
import re
import time

import requests

USER = 'user@example.com'
PASS = 'secret'
NOTIFY_TOKENS = ['eins', 'zwei', 'drei']

session = requests.Session()

print('Logging in...')

session.get('https://ezakupy.tesco.pl/groceries/pl-PL/')
resp = session.get('https://ezakupy.tesco.pl/groceries/pl-PL/login',
                   params={'from': 'https://ezakupy.tesco.pl/groceries/pl-PL/'})

match = re.search('data-csrf-token="([^"]+)"', resp.text)
csrf_token = match.group(1)

resp = session.post('https://ezakupy.tesco.pl/groceries/pl-PL/login',
             params={'from': 'https://ezakupy.tesco.pl/groceries/pl-PL/'},
             data={
                 'email': USER,
                 'password': PASS,
                 'onSuccessUrl': 'https://ezakupy.tesco.pl/groceries/pl-PL/',
                 '_csrf': csrf_token
                 })
assert resp.ok

print('Logged in.')

try:
    with open('tesco.dat', 'br') as f:
        last_available = pickle.load(f)
    print('Loaded last available:')
    for slot in sorted(last_available):
        print(' * %s' % slot)
except Exception as e:
    print('Error loading last available: %s' % e)
    last_available = set()

try:
    while True:
        resp = session.get('https://ezakupy.tesco.pl/groceries/pl-PL/slots/delivery')
        assert resp.ok

        day = date.today()

        # find last Sunday
        #while day.weekday() != 6:
        #    day -= timedelta(1)

        available = set()

        for _ in range(3):
            print('Checking available slots in the week of %s' % day)
            resp = session.get('https://ezakupy.tesco.pl/groceries/pl-PL/slots/delivery/%s' % day,
                    params={'slotGroup': 2}, headers={'accept': 'application/json'})
            assert resp.ok

            slots = resp.json()['slots']
            slots = [slot for slot in slots if slot.get('status') != 'UnAvailable']
            available |= set(slot['start'] for slot in slots)

            if slots:
                if False:
                    with open('tesco-%s.json' % str(datetime.utcnow()), 'w', encoding='utf-8') as f:
                        f.write(json.dumps(resp.json()))
            day += timedelta(7)

        new_available = available - last_available

        print('Slots found:', len(available))
        for slot in sorted(available):
            print(' * %s' % slot)

        print('New slots:', len(new_available))
        for slot in sorted(new_available):
            print(' * %s' % slot)

        if new_available:
            if len(new_available) == 1:
                text = 'Nowy termin dostawy w Tesco: %s' % new_available[0]
            else:
                first = min(new_available)
                last = max(new_available)
                text = 'Nowe terminy dostawy w Tesco (%i), pierwszy %s, ostatni %s' % (len(new_available), first, last)

            for token in NOTIFY_TOKENS:
                requests.get('https://wirepusher.com/send',
                             params={
                                 'id': token,
                                 'title': 'Tesco',
                                 'message': text,
                                 'type': 'tesco'
                            })

        last_available = available
        print('Sleeping...')
        time.sleep(random.randint(30, 180))
except KeyboardInterrupt:
    raise SystemExit
finally:
    with open('tesco.dat', 'wb') as f:
        pickle.dump(last_available, f)
