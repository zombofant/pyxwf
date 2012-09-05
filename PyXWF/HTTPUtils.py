import re
import email.utils as eutils
from datetime import datetime
from wsgiref.handlers import format_date_time

import PyXWF.TimeUtils as TimeUtils

def parse_http_date(httpdate):
    """
    Parse the string *httpdate* as a date according to RFC 2616 and return the
    resulting :class:`~datetime.datetime` instance.

    .. note::
        This uses :func:`email.utils.parsedate`.
    """
    return datetime(*eutils.parsedate(httpdate)[:6])

def format_http_date(datetime):
    """
    Convert the :class:`~datetime.datetime` instance *datetime* into a string
    formatted to be compliant with the HTTP RFC.

    .. note::
        This uses :func:`wsgiref.handlers.format_date_time`.
    """
    return format_date_time(TimeUtils.to_timestamp(datetime))
