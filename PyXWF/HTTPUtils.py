import re
import email.utils as eutils
from datetime import datetime
from wsgiref.handlers import format_date_time

import PyXWF.TimeUtils as TimeUtils

def parseHTTPDate(httpDate):
    """
    Parse the string *httpDate* as a date according to RFC 2616 and return the
    resulting :class:`~datetime.datetime` instance.

    .. note::
        This uses :func:`email.utils.parsedate`.
    """
    return datetime(*eutils.parsedate(httpDate)[:6])

def formatHTTPDate(datetime):
    """
    Convert the :class:`~datetime.datetime` instance *datetime* into a string
    formatted to be compliant with the HTTP RFC.

    .. note::
        This uses :func:`wsgiref.handlers.format_date_time`.
    """
    return format_date_time(TimeUtils.toTimestamp(datetime))
