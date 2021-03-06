# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
import locale
from json import dumps
from functools import wraps
from datetime import datetime
from lxml import etree
from flask import Response
from presence_analyzer.main import app
from time import time as cur_time
from threading import Lock

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103

CACHE = {}
LOCKER = Lock()


def locker(fun):
    """
    Locks thread.
    """
    def _locker():
        with LOCKER:
            return fun()
    return _locker


def cache(duration, key):
    """
    Caches function result for given amount of time (in seconds).
    """
    def _cache(fun):
        def __cache():
            if (key not in CACHE or
               cur_time() > CACHE[key]['time']):
                CACHE[key] = {
                    'data': fun(),
                    'time': cur_time()+duration
                }
            return CACHE[key]['data']
        return __cache
    return _cache


def get_data_xml():
    """
    Parses data from XML file (server and users info).
    """
    xml_file = etree.parse(app.config['DATA_XML']).getroot()
    server = {
        'host': xml_file.findtext('.//host'),
        'port': xml_file.findtext('.//port'),
        'protocol': xml_file.findtext('.//protocol')
    }

    users_xml = {
        user.attrib['id']: {
            'user_id': user.attrib['id'],
            'avatar': "{}://{}{}".format(
                server['protocol'],
                server['host'],
                user.findtext('avatar')
            ),
            'name': unicode(user.findtext('name'))
        }
        for user in xml_file.findall('.//user')
    }

    locale.setlocale(locale.LC_ALL, 'pl_PL.utf-8')
    users_xml = sorted(
        users_xml.iteritems(),
        cmp=lambda user1, user2: locale.strcoll(
            user1[1]['name'],
            user2[1]['name']
        )
    )
    locale.setlocale(locale.LC_ALL, (None, None))

    return users_xml


def jsonify(function):
    """
    Creates a response with the JSON representation of wrapped function result.
    """
    @wraps(function)
    def inner(*args, **kwargs):
        return Response(dumps(function(*args, **kwargs)),
                        mimetype='application/json')
    return inner


@locker
@cache(600, 0)
def get_data():
    """
    Extracts presence data from CSV file and groups it by user_id.

    It creates structure like this:
    data = {
        'user_id': {
            datetime.date(2013, 10, 1): {
                'start': datetime.time(9, 0, 0),
                'end': datetime.time(17, 30, 0),
            },
            datetime.date(2013, 10, 2): {
                'start': datetime.time(8, 30, 0),
                'end': datetime.time(16, 45, 0),
            },
        }
    }
    """
    data = {}
    with open(app.config['DATA_CSV'], 'r') as csvfile:
        presence_reader = csv.reader(csvfile, delimiter=',')
        for i, row in enumerate(presence_reader):
            if len(row) != 4:
                # ignore header and footer lines
                continue

            try:
                user_id = int(row[0])
                date = datetime.strptime(row[1], '%Y-%m-%d').date()
                start = datetime.strptime(row[2], '%H:%M:%S').time()
                end = datetime.strptime(row[3], '%H:%M:%S').time()
            except (ValueError, TypeError):
                log.debug('Problem with line %d: ', i, exc_info=True)

            data.setdefault(user_id, {})[date] = {'start': start, 'end': end}

    return data


def group_by_weekday(items):
    """
    Groups presence entries by weekday.
    """
    result = {i: [] for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()].append(interval(start, end))
    return result


def group_start_end_by_weekday(items):
    """
    Groups starts and ends by weekday
    """
    result = {i: {'start': [], 'end': []} for i in range(7)}
    for date in items:
        start = items[date]['start']
        end = items[date]['end']
        result[date.weekday()]['start'].append(start)
        result[date.weekday()]['end'].append(end)
    return result


def seconds_since_midnight(time):
    """
    Calculates amount of seconds since midnight.
    """
    return time.hour * 3600 + time.minute * 60 + time.second


def interval(start, end):
    """
    Calculates inverval in seconds between two datetime.time objects.
    """
    return seconds_since_midnight(end) - seconds_since_midnight(start)


def mean(items):
    """
    Calculates arithmetic mean. Returns zero for empty lists.
    """
    return float(sum(items)) / len(items) if len(items) > 0 else 0
