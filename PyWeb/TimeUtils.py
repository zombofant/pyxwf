from datetime import datetime, timedelta
from calendar import timegm

monthname = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def toTimestamp(datetime):
    return timegm(datetime.utctimetuple())
    
def toDatetime(timestamp):
    return datetime.utcfromtimestamp(timestamp)
    
def nowDate():
    return datetime.utcnow()
    
def now():
    return toTimestamp(nowDate())

def nextMonth(dt):
    if dt.month == 12:
        return datetime(year=dt.year+1, month=1, day=1)
    else:
        return datetime(year=dt.year, month=dt.month+1, day=1)

def monthTimeRange(year, month):
    first = datetime(year, month, 1)
    return (toTimestamp(first), toTimestamp(nextMonth(first)))

def yearTimeRange(year):
    return (toTimestamp(datetime(year, 1, 1)), toTimestamp(datetime(year+1, 1, 1)))

def calendarTimeRange(year, month=None):
    if month is not None:
        return monthTimeRange(year, month)
    else:
        return yearTimeRange(year)
        
def normalizeDate(dateTime):
    return datetime(year=dateTime.year, month=dateTime.month, day=dateTime.day)

fromTimestamp = toDatetime
