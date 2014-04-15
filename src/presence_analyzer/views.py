# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from presence_analyzer.main import app
from flask import url_for
from lxml import etree
from flask import redirect
from flask import Flask
from flask.ext.mako import MakoTemplates
from flask.ext.mako import render_template
from flask.helpers import make_response
from mako.exceptions import TopLevelLookupException
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean, group_by_weekday,
    seconds_since_midnight,
    group_start_end_by_weekday
)
import os.path


import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103
mako = MakoTemplates(app)


users_info = {}
server = {'host': '', 'port': '', 'protocol': ''}

@app.before_first_request
def get_urls(*args, **kwargs):
    XML_file = etree.parse(
        os.path.abspath(
            'src/presence_analyzer/' + url_for('static', filename='data/users_info.xml')
            )
        ).getroot()
    
    for data_type in XML_file:
        for data in data_type:
            # Parse users info.
            if data_type.tag == 'users':
                user_id = int(data.attrib['id'])
                users_info[user_id] = {'avatar': '', 'name': ''}
                for info in data:
                    if info.tag == 'avatar':
                        users_info[user_id]['avatar'] = info.text
                    elif info.tag == 'name':
                        users_info[user_id]['name'] = unicode(info.text)
            # Parse server info.
            elif data_type.tag == 'server':
                server[data.tag] = data.text



@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/templates/presence_weekday')


@app.route('/api/v1/get_photo/<int:user_id>', methods=['GET'])
@jsonify
def get_photo(user_id):
    """
    Returns user's photo url
    """
    return "{protocol}://{host}:{port}{avatar}".format(
            protocol=server['protocol'],
            host=server['host'],
            port=server['port'],
            avatar=users_info[user_id]['avatar']
        )


@app.route('/templates/<string:template>')
def template_handler(template):
    """
    Handles generating templates.
    """
    try:
        return render_template(template+'.html')
    except TopLevelLookupException:
        return make_response('This page does not exist', 404)


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [{'user_id': i, 'name': users_info[i]['name']}
            if i in users_info.keys()
            else {'user_id': i, 'name': 'Unknown user: {}'.format(i)}
            for i in data.keys()]


@app.route('/api/v1/mean_time_weekday/<int:user_id>', methods=['GET'])
@jsonify
def mean_time_weekday_view(user_id):
    """
    Returns mean presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], mean(intervals))
              for weekday, intervals in weekdays.items()]

    return result


@app.route('/api/v1/presence_weekday/<int:user_id>', methods=['GET'])
@jsonify
def presence_weekday_view(user_id):
    """
    Returns total presence time of given user grouped by weekday.
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_by_weekday(data[user_id])
    result = [(calendar.day_abbr[weekday], sum(intervals))
              for weekday, intervals in weekdays.items()]

    result.insert(0, ('Weekday', 'Presence (s)'))
    return result


@app.route('/api/v1/presence_start_end/<int:user_id>', methods=['GET'])
@jsonify
def presence_start_end_view(user_id):
    """
    Returns mean start and end time of work for user
    """
    data = get_data()
    if user_id not in data:
        log.debug('User %s not found!', user_id)
        return []

    weekdays = group_start_end_by_weekday(data[user_id])

    result = [[
        calendar.day_abbr[day_number],
        mean([seconds_since_midnight(start) for start in day['start']]),
        mean([seconds_since_midnight(end) for end in day['end']])
    ] for day_number, day in weekdays.items()]

    return result
