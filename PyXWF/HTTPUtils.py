# File name: HTTPUtils.py
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
