import re
import email.utils as eutils
from datetime import datetime
from wsgiref.handlers import format_date_time

import PyXWF.TimeUtils as TimeUtils

"""
Sun, 06 Nov 1994 08:49:37 GMT  ; RFC 822, updated by RFC 1123
Sunday, 06-Nov-94 08:49:37 GMT ; RFC 850, obsoleted by RFC 1036
Sun Nov  6 08:49:37 1994       ; ANSI C's asctime() format
"""

def parseHTTPDate(httpDate):
    return datetime(*eutils.parsedate(httpDate)[:6])

def formatHTTPDate(datetime):
    return format_date_time(TimeUtils.toTimestamp(datetime))
