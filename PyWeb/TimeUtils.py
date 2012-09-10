"""
Some helper functions for dealing with time issues (especially converting
from/to local timezone to/from utc).
"""

from datetime import datetime, timedelta
from calendar import timegm

monthname = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def toTimestamp(datetime):
    """
    Convert *datetime* to a UTC unix timestamp.
    """
    return timegm(datetime.utctimetuple())

def toDatetime(timestamp):
    """
    Convert a timestamp like returned by :func:`toTimestamp` to a utc datetime
    object.
    """
    return datetime.utcfromtimestamp(timestamp)

def nowDate():
    """
    The current time in UTC as datetime object.
    """
    return datetime.utcnow()

def now():
    """
    The current time in UTC as unix timestamp.
    """
    return toTimestamp(nowDate())

def nextMonth(dt):
    """
    Get the datetime representing the first day of the month after the month
    set in *dt*.
    """
    if dt.month == 12:
        return datetime(year=dt.year+1, month=1, day=1)
    else:
        return datetime(year=dt.year, month=dt.month+1, day=1)

def normalizeDate(dateTime):
    """
    Returns a plain date (with time information reset to midnight) from the
    given *dateTime* object.
    """
    return datetime(year=dateTime.year, month=dateTime.month, day=dateTime.day)

def stripMicroseconds(dateTime):
    """
    Remove microseconds from the given *dateTime* object.
    """
    return datetime(
        dateTime.year,
        dateTime.month,
        dateTime.day,
        dateTime.hour,
        dateTime.minute,
        dateTime.second
    )

fromTimestamp = toDatetime
