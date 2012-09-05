from __future__ import unicode_literals

import unittest
from datetime import datetime

import PyXWF.TimeUtils as TimeUtils

class Timestamp2Datetime(unittest.TestCase):
    def test_roundtrip(self):
        # this will probably only trigger in non-UTC timezones!
        dt = TimeUtils.strip_microseconds(TimeUtils.now_date())
        self.assertEqual(dt, TimeUtils.to_datetime(TimeUtils.to_timestamp(dt)))

class strip_microseconds(unittest.TestCase):
    def test_strip(self):
        dt = datetime(year=2012, month=8, day=24,
                      hour=10, minute=37, second=23, microsecond=10)
        self.assertEqual(TimeUtils.strip_microseconds(dt),
            datetime(
                year=2012,
                month=8,
                day=24,
                hour=10,
                minute=37,
                second=23,
            )
        )

class normalize_date(unittest.TestCase):
    def test_strip(self):
        dt = datetime(year=2012, month=8, day=24,
                      hour=10, minute=38, second=16, microsecond=10)
        self.assertEqual(TimeUtils.normalize_date(dt),
            datetime(
                year=2012,
                month=8,
                day=24,
            )
        )


class next_month(unittest.TestCase):
    def test_next(self):
        dt = datetime(year=2012, month=8, day=24, hour=10)
        self.assertEqual(TimeUtils.next_month(dt),
            datetime(year=2012, month=9, day=1)
        )

    def test_wrap(self):
        dt = datetime(year=2012, month=12, day=24, hour=10)
        self.assertEqual(TimeUtils.next_month(dt),
            datetime(year=2013, month=1, day=1)
        )
