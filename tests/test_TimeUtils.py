# File name: test_TimeUtils.py
# This file is part of: pyxwf
#
# LICENSE
#
# The contents of this file are subject to the Mozilla Public License
# Version 1.1 (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://www.mozilla.org/MPL/
#
# Software distributed under the License is distributed on an "AS IS"
# basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See
# the License for the specific language governing rights and limitations
# under the License.
#
# Alternatively, the contents of this file may be used under the terms
# of the GNU General Public license (the  "GPL License"), in which case
# the provisions of GPL License are applicable instead of those above.
#
# FEEDBACK & QUESTIONS
#
# For feedback and questions about pyxwf please e-mail one of the
# authors named in the AUTHORS file.
########################################################################
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
