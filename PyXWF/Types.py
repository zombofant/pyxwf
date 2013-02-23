# encoding=utf-8
# File name: Types.py
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
Some awesome typecasts.
"""
from __future__ import unicode_literals

import PyXWF.utils as utils
from datetime import datetime, timedelta

class WrapFunction(object):
    def __init__(self, func, description):
        self.func = func
        self.description = description

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __str__(self):
        return str(self.description)

    def __unicode__(self):
        return self.description

bool_names = {
    "false": False,
    "no": False,
    "off": False,
    "true": True,
    "yes": True,
    "on": True
}

def _bool_helper(value):
    global bool_names
    if isinstance(value, (int, long, float)):
        return bool(value)
    elif isinstance(value, basestring):
        try:
            return bool_names[value.lower()]
        except KeyError:
            pass
    elif isinstance(value, bool):
        return value
    raise ValueError("Not a valid boolean: {0!r}".format(value))

def _empty_helper(value):
    if not isinstance(value, basestring):
        value = unicode(value)
    value = value.strip()
    if len(value) > 0:
        raise ValueError("{0!r} is not empty".format(value))
    return value

def NumericRange(typecast, min, max):
    if min is None and max is None:
        return typecast
    elif min is None:
        range_str = "-∞..{0}".format(max)
        def tc(value):
            numeric = typecast(value)
            if value > max:
                raise ValueError("numeric value {0} out of bounds: {1}".format(
                    numeric, range_str
                ))
            return numeric
    elif max is None:
        range_str = "{0}..∞".format(min)
        def tc(value):
            numeric = typecast(value)
            if value < min:
                raise ValueError("numeric value {0} out of bounds: {1}".format(
                    numeric, range_str
                ))
            return numeric
    else:
        range_str = "{0}..{1}".format(min, max)
        def tc(value):
            numeric = typecast(value)
            if not (min <= numeric <= max):
                raise ValueError("numeric value {0} out of bounds: {1}".format(
                    numeric, range_str
                ))
            return numeric
    return WrapFunction(tc, "{0} within a range of {1}".format(
        unicode(typecast), range_str
    ))

def AllowBoth(type1, type2):
    def redefine_both_callable(s):
        try:
            return type1(s)
        except Exception as e1:
            try:
                return type2(s)
            except Exception as e2:
                raise ValueError("{0} and {1}".format(e1, e2))
    return WrapFunction(redefine_both_callable,
        "{0} or {1}".format(unicode(type1), unicode(type2))
    )

def DefaultForNone(default, typecast=None):
    if typecast is None:
        def tc(value):
            if value is None:
                return default
            else:
                return value
        return WrapFunction(tc,
            "any value, defaults to {0!r} for None".format(default))
    else:
        def tc(value):
            if value is None:
                return default
            else:
                return typecast(value)
        return WrapFunction(tc,
            "{0}, defaults to {1!r} for None".format(
                unicode(typecast), default
            )
        )

def EnumMap(mapping):
    def valid_values():
        return ", ".join(repr(v) for v in mapping.viewkeys())
    def tc(value, **kwargs):
        try:
            if value is None and "default" in kwargs:
                return kwargs["default"]
            else:
                return mapping[value]
        except KeyError as err:
            raise ValueError("{0!r} is invalid, must be one of {1}".format(
                value, valid_values()
            ))
    return WrapFunction(tc, "one of {0}".format(valid_values()))

def _not_none_helper(v):
    if v is None:
        raise ValueError("Value is None")
    return v

NotNone = WrapFunction(_not_none_helper, "not none")

def _not_empty(v):
    if len(v) == 0:
        raise ValueError("Value is empty")
    return v

NotEmpty = WrapFunction(_not_empty, "not empty")

class Typecasts(object):
    int = WrapFunction(int, "integer number")
    long = WrapFunction(long, "integer number")
    float = WrapFunction(float, "decimal number")
    unicode = WrapFunction(unicode, "character string")
    str = WrapFunction(str, "character string")
    bool = WrapFunction(_bool_helper , """boolean value (e.g. "true" or "false")""")
    empty_string = WrapFunction(_empty_helper, "empty string")
