# -*- coding: utf-8 -*-
"""
Helper functions used in views.
"""

import csv
from json import dumps
from functools import wraps
from datetime import datetime
from lxml import etree
from flask import Response
from flask import url_for
from presence_analyzer.main import app

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103


def get_data_xml(*args, **kwargs):
    """
    Parses data from XML file (server and users info).
    """
    users = get_data()
    xml_file = etree.parse(app.config['DATA_XML']).getroot()
    users_xml = {}
    server = {'host': '', 'port': '', 'protocol': ''}

    for data_type in xml_file:
        for data in data_type:
            # Parse users info.
            if data_type.tag == 'users':
                user_id = data.attrib['id']
                users_xml[user_id] = {
                    'user_id': user_id,
                    'avatar': '',
                    'name': ''
                }
                for info in data:
                    if info.tag == 'avatar':
                        users_xml[user_id]['avatar'] = "{}://{}{}".format(
                            server['protocol'],
                            server['host'],
                            info.text
                        )
                    elif info.tag == 'name':
                        users_xml[user_id]['name'] = unicode(info.text)
            # Parse SERVER info.
            elif data_type.tag == 'server':
                server[data.tag] = data.text

    for user_id in users:
        if str(user_id) not in users_xml:
            users_xml[str(user_id)] = {
                'user_id': str(user_id),
                'avatar': url_for('static', filename='img/no_avatar.png'),
                'name': u'Unknown user: {}'.format(str(user_id))
            }

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
