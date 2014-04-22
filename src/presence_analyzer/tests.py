# -*- coding: utf-8 -*-
"""
Presence analyzer unit tests.
"""
import os.path
import json
import datetime
import unittest

from presence_analyzer import main, views, utils


TEST_DATA_CSV = os.path.join(
    os.path.dirname(__file__), '..', '..', 'runtime', 'data', 'test_data.csv'
)

TEST_CACHE_DATA_CSV1 = os.path.join(
    os.path.dirname(__file__),
    '..', '..', 'runtime', 'data', 'test_data_cache1.csv'
)

TEST_DATA_XML = os.path.join(
    os.path.dirname(__file__),
    '..', '..', 'runtime', 'data', 'users_test.xml'
)


# pylint: disable=E1103
class PresenceAnalyzerViewsTestCase(unittest.TestCase):
    """
    Views tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        main.app.config.update({'DATA_XML': TEST_DATA_XML})
        self.client = main.app.test_client()

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_mainpage(self):
        """
        Test main page redirect.
        """
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        assert resp.headers['Location'].endswith('/presence_weekday')

    def test_api_users(self):
        """
        Test users listing.
        """
        resp = self.client.get('/api/v2/users')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 2)
        self.assertDictEqual(data, {
            u'176': {
                u'user_id': u'176',
                u'avatar': u'https://intranet.stxnext.pl/api/images/users/176',
                u'name': u'Adrian K.'
                },
            u'141': {
                u'user_id': u'141',
                u'avatar': u'https://intranet.stxnext.pl/api/images/users/141',
                u'name': u'Adam P.'
                }
            }
        )

    def test_mean_time_weekday_view(self):
        """
        Test mean time by weekday view
        """
        resp = self.client.get('/api/v1/mean_time_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertItemsEqual(data, [
            [u'Mon', 0],
            [u'Tue', 30047.0],
            [u'Wed', 24465.0],
            [u'Thu', 23705.0],
            [u'Fri', 0],
            [u'Sat', 0],
            [u'Sun', 0]
            ]
        )

    def test_presence_weekday_view(self):
        """
        Test presence by weekday view
        """
        resp = self.client.get('/api/v1/presence_weekday/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 8)
        self.assertItemsEqual(data, [
            [u'Weekday', u'Presence (s)'],
            [u'Mon', 0],
            [u'Tue', 30047],
            [u'Wed', 24465],
            [u'Thu', 23705],
            [u'Fri', 0],
            [u'Sat', 0],
            [u'Sun', 0]
            ]
        )

    def test_presence_start_end_view(self):
        """
        Test presence start, end view
        """
        resp = self.client.get('/api/v1/presence_start_end/10')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.content_type, 'application/json')
        data = json.loads(resp.data)
        self.assertEqual(len(data), 7)
        self.assertEqual(data, [
            [u'Mon', 0, 0],
            [u'Tue', 34745.0, 64792.0],
            [u'Wed', 33592.0, 58057.0],
            [u'Thu', 38926.0, 62631.0],
            [u'Fri', 0, 0],
            [u'Sat', 0, 0],
            [u'Sun', 0, 0]
            ]
        )


class PresenceAnalyzerUtilsTestCase(unittest.TestCase):
    """
    Utility functions tests.
    """

    def setUp(self):
        """
        Before each test, set up a environment.
        """
        main.app.config.update({'DATA_CSV': TEST_DATA_CSV})
        utils.CACHE = {}

    def tearDown(self):
        """
        Get rid of unused objects after each test.
        """
        pass

    def test_get_data(self):
        """
        Test parsing of CSV file.
        """
        data = utils.get_data()
        self.assertIsInstance(data, dict)
        self.assertItemsEqual(data.keys(), [10, 11])
        sample_date = datetime.date(2013, 9, 10)
        self.assertIn(sample_date, data[10])
        self.assertItemsEqual(data[10][sample_date].keys(), ['start', 'end'])
        self.assertEqual(data[10][sample_date]['start'],
                         datetime.time(9, 39, 5))

    def test_group_by_weekday(self):
        """
        Test grouping by weekday.
        """
        data = utils.get_data()

        result = utils.group_by_weekday(data[10])
        self.assertItemsEqual(result, {
            0: [],
            1: [30047],
            2: [24465],
            3: [23705],
            4: [],
            5: [],
            6: []
            }
        )

    def test_seconds_since_midnight(self):
        """
        Test calculating time that passed since midnight
        """
        result = utils.seconds_since_midnight(datetime.time(9, 10, 15))
        self.assertEqual(result, 33015)

        result = utils.seconds_since_midnight(datetime.time(0, 0, 0))
        self.assertEqual(result, 0)

        result = utils.seconds_since_midnight(datetime.time(12, 10, 15))
        self.assertEqual(result, 43815)

    def test_interval(self):
        """
        Test calculating interval between times
        """
        result = utils.interval(datetime.time(9, 10, 15),
                                datetime.time(9, 10, 20))
        self.assertEqual(result, 5)

        result = utils.interval(datetime.time(7, 11, 15),
                                datetime.time(9, 10, 20))
        self.assertEqual(result, 7145)

        result = utils.interval(datetime.time(7, 11, 15),
                                datetime.time(19, 00, 00))
        self.assertEqual(result, 42525)

    def test_mean(self):
        """
        Test calculating mean
        """
        result = utils.mean([1, 2, 3, 4, 5])
        self.assertEqual(result, 3)

        result = utils.mean([1, 2, 3, 4])
        self.assertEqual(result, 2.5)

        result = utils.mean([])
        self.assertEqual(result, 0)

    def test_group_start_end_by_weekday(self):
        """
        Test grouping starts and ends by weekday
        """
        data = utils.get_data()

        result = utils.group_start_end_by_weekday(data[10])
        self.assertDictContainsSubset(result, {
            0: {'end': [], 'start': []},
            1: {
                'end': [datetime.time(17, 59, 52)],
                'start': [datetime.time(9, 39, 5)]
                },
            2: {
                'end': [datetime.time(16, 7, 37)],
                'start': [datetime.time(9, 19, 52)]
                },
            3: {
                'end': [datetime.time(17, 23, 51)],
                'start': [datetime.time(10, 48, 46)]
                },
            4: {'end': [], 'start': []},
            5: {'end': [], 'start': []},
            6: {'end': [], 'start': []}}
        )

    def test_get_data_cache(self):
        data = utils.get_data()
        self.assertDictEqual(data, utils.CACHE[0]['data'])

        main.app.config.update({'DATA_CSV': TEST_CACHE_DATA_CSV1})
        data = utils.get_data()
        self.assertDictEqual(data, utils.CACHE[0]['data'])

        utils.CACHE = {}

        data = utils.get_data()
        self.assertDictEqual(data, utils.CACHE[0]['data'])


def suite():
    """
    Default test suite.
    """
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(PresenceAnalyzerViewsTestCase))
    suite.addTest(unittest.makeSuite(PresenceAnalyzerUtilsTestCase))
    return suite


if __name__ == '__main__':
    unittest.main()
