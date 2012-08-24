from __future__ import unicode_literals

import unittest
from datetime import datetime

import PyWeb.TimeUtils as TimeUtils

class Timestamp2Datetime(unittest.TestCase):
    def test_roundtrip(self):
        # this will probably only trigger in non-UTC timezones!
        dt = TimeUtils.stripMicroseconds(TimeUtils.nowDate())
        self.assertEqual(dt, TimeUtils.toDatetime(TimeUtils.toTimestamp(dt)))

class stripMicroseconds(unittest.TestCase):
    def test_strip(self):
        dt = datetime(year=2012, month=8, day=24,
                      hour=10, minute=37, second=23, microsecond=10)
        self.assertEqual(TimeUtils.stripMicroseconds(dt),
            datetime(
                year=2012,
                month=8,
                day=24,
                hour=10,
                minute=37,
                second=23,
            )
        )

class normalizeDate(unittest.TestCase):
    def test_strip(self):
        dt = datetime(year=2012, month=8, day=24,
                      hour=10, minute=38, second=16, microsecond=10)
        self.assertEqual(TimeUtils.normalizeDate(dt),
            datetime(
                year=2012,
                month=8,
                day=24,
            )
        )


class nextMonth(unittest.TestCase):
    def test_next(self):
        dt = datetime(year=2012, month=8, day=24, hour=10)
        self.assertEqual(TimeUtils.nextMonth(dt),
            datetime(year=2012, month=9, day=1)
        )

    def test_wrap(self):
        dt = datetime(year=2012, month=12, day=24, hour=10)
        self.assertEqual(TimeUtils.nextMonth(dt),
            datetime(year=2013, month=1, day=1)
        )
