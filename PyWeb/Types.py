# encoding=utf-8
"""
Some awesome typecasts.
"""
from __future__ import unicode_literals

import PyWeb.utils as utils
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

boolNames = {
    "false": False,
    "no": False,
    "off": False, 
    "true": True,
    "yes": True,
    "on": True
}

def _boolHelper(value):
    global boolNames
    if isinstance(value, (int, long, float)):
        return bool(value)
    elif isinstance(value, basestring):
        try:
            return boolNames[value.lower()]
        except KeyError:
            pass
    raise ValueError("Not a valid boolean: {0!r}".format(value))

def _emptyHelper(value):
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
        rangeStr = "-∞..{0}".format(max)
        def tc(value):
            numeric = typecast(value)
            if value > max:
                raise ValueError("numeric value {0} out of bounds: {1}".format(
                    numeric, rangeStr
                ))
            return numeric
    elif max is None:
        rangeStr = "{0}..∞".format(min)
        def tc(value):
            numeric = typecast(value)
            if value < min:
                raise ValueError("numeric value {0} out of bounds: {1}".format(
                    numeric, rangeStr
                ))
            return numeric
    else:
        rangeStr = "{0}..{1}".format(min, max)
        def tc(value):
            numeric = typecast(value)
            if not min <= value <= max:
                raise ValueError("numeric value {0} out of bounds: {1}".format(
                    numeric, rangeStr
                ))
            return numeric
    return WrapFunction(tc, "{0} within a range of {1}".format(
        unicode(typecast), rangeStr
    ))

def AllowBoth(type1, type2):
    def redefine_both_callable(s):
        try:
            return type1(s)
        except Exception as e1:
            try:
                return type2(s)
            except Exception as e2:
                raise ValueError("{1} and {2}".format(e1, e2))
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
    def validValues():
        return ", ".join(repr(v) for v in mapping.viewkeys())
    def tc(value, **kwargs):
        try:
            if value is None and "default" in kwargs:
                return kwargs["default"]
            else:
                return mapping[value]
        except KeyError as err:
            raise ValueError("{0!r} is invalid, must be one of {1}".format(
                value, validValues()
            ))
    return WrapFunction(tc, "one of {0}".format(validValues()))

class Typecasts(object):
    int = WrapFunction(int, "integer number")
    long = WrapFunction(long, "integer number")
    float = WrapFunction(float, "decimal number")
    unicode = WrapFunction(unicode, "character string")
    str = WrapFunction(str, "character string")
    bool = WrapFunction(_boolHelper , """boolean value (e.g. "true" or "false")""")
    emptyString = WrapFunction(_emptyHelper, "empty string")
