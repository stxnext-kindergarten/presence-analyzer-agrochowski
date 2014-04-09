# -*- coding: utf-8 -*-
"""
Defines views.
"""

import calendar
from flask import redirect
from flask.ext.mako import MakoTemplates
from flask.ext.mako import render_template
from presence_analyzer.main import app
from presence_analyzer.utils import (
    jsonify,
    get_data,
    mean, group_by_weekday,
    seconds_since_midnight,
    group_start_end_by_weekday
)

import logging
log = logging.getLogger(__name__)  # pylint: disable-msg=C0103
mako = MakoTemplates(app)


@app.route('/')
def mainpage():
    """
    Redirects to front page.
    """
    return redirect('/templates/presence_weekday')


@app.route('/templates/presence_start_end')
def presence_start_end_template():
    """
    Generates template for presence_start_end view
    """
    return render_template('presence_start_end.html',
                           index='Presence start-end')


@app.route('/templates/mean_time_weekday')
def mean_time_weekday_template():
    """
    Generates template for mean_time_weekday view
    """
    return render_template('mean_time_weekday.html',
                           index='Presence mean time')


@app.route('/templates/presence_weekday')
def presence_weekday_template():
    """
    Generates template for presence_weekday view
    """
    return render_template('presence_weekday.html',
                           index='Presence by weekday')


@app.route('/api/v1/users', methods=['GET'])
@jsonify
def users_view():
    """
    Users listing for dropdown.
    """
    data = get_data()
    return [{'user_id': i, 'name': 'User {0}'.format(str(i))}
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
