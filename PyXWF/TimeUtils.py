# File name: TimeUtils.py
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
"""
Some helper functions for dealing with time issues (especially converting
from/to local timezone to/from utc).
"""

from datetime import datetime, timedelta
from calendar import timegm

monthname = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def to_timestamp(datetime):
    """
    Convert *datetime* to a UTC unix timestamp.
    """
    return timegm(datetime.utctimetuple())

def to_datetime(timestamp):
    """
    Convert a timestamp like returned by :func:`to_timestamp` to a utc datetime
    object.
    """
    return datetime.utcfromtimestamp(timestamp)

def now_date():
    """
    The current time in UTC as datetime object.
    """
    return datetime.utcnow()

def now():
    """
    The current time in UTC as unix timestamp.
    """
    return to_timestamp(now_date())

def next_month(dt):
    """
    Get the datetime representing the first day of the month after the month
    set in *dt*.
    """
    if dt.month == 12:
        return datetime(year=dt.year+1, month=1, day=1)
    else:
        return datetime(year=dt.year, month=dt.month+1, day=1)

def normalize_date(date_time):
    """
    Returns a plain date (with time information reset to midnight) from the
    given *date_time* object.
    """
    return datetime(year=date_time.year, month=date_time.month, day=date_time.day)

def strip_microseconds(date_time):
    """
    Remove microseconds from the given *date_time* object.
    """
    return datetime(
        date_time.year,
        date_time.month,
        date_time.day,
        date_time.hour,
        date_time.minute,
        date_time.second
    )

from_timestamp = to_datetime
