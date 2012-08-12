"""
XML namespace magic. The classes defined in this module have special
``__getattr__`` implementations, which will return a string containing the
name of the attribute asked for prefixed with the ElementTree representation
of the namespace of the class. The only exception is the `xmlns` attribute which
will return the namespace itself.
"""

import PyWeb.utils as utils

class __metaclass__(utils.NoInstance):
    """
    Metaclass for namespace classes. Namespace classes must have an *xmlns*
    attribute which is the XML namespace they're representing. They may have
    a *cache* attribute which must be an iterable of strings. The contained
    strings will be precached.
    """
    def __new__(mcls, name, bases, dct):
        cache = dct.get("cache", list())
        dct["cache"] = dict()
        cls = super(__metaclass__, mcls).__new__(mcls, name, bases, dct)
        # prepopulate cache
        for entry in cache:
            getattr(cls, entry)
        dct["cache"]["xmlns"] = dct["xmlns"]
        return cls

    def __getattr__(cls, name):
        cache = cls.__dict__["cache"]
        try:
            return cache[name]
        except KeyError:
            attr = "{{{0}}}{1}".format(cls.xmlns, name)
            cache[name] = attr
        return attr

    def __str__(cls):
        return cls.__dict__["xmlns"]

    def __unicode__(cls):
        return unicode(cls.__dict__["xmlns"])


class XHTML(object):
    __metaclass__ = __metaclass__
    xmlns = "http://www.w3.org/1999/xhtml"
    cache = ["a", "head", "title", "body"]

xhtml = XHTML

class PyWebXML(object):
    __metaclass__ = __metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/documents/pywebxml"
    cache = ["a"]

class Site(object):
    __metaclass__ = __metaclass__
    xmlns = "http://pyweb.zombofant.net/xmlns/site"
    cache = ["meta", "site", "tree"]
