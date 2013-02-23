# File name: Namespaces.py
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
XML namespace magic. The classes defined in this module have special
``__getattr__`` implementations, which will return a string containing the
name of the attribute asked for prefixed with the ElementTree representation
of the namespace of the class. The only exception is the `xmlns` attribute which
will return the namespace itself.
"""

import lxml.builder as builder
import PyXWF.utils as utils

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
        dct["cache"]["maker"] = builder.ElementMaker(namespace=dct["xmlns"])
        return cls

    def __call__(cls, name, *args, **kwargs):
        return getattr(cls.__dict__["cache"]["maker"], name)(*args, **kwargs)

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
    xmlns = "http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
    cache = ["a"]

class LocalR(object):
    __metaclass__ = __metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/href/localr"
    cache = ["href", "src"]

class LocalG(object):
    __metaclass__ = __metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/href/localg"
    cache = ["href", "src"]

class Site(object):
    __metaclass__ = __metaclass__
    xmlns = "http://pyxwf.zombofant.net/xmlns/site"
    cache = ["meta", "site", "tree"]

class Atom(object):
    __metaclass__ = __metaclass__
    xmlns = "http://www.w3.org/2005/Atom"

utils.ET.register_namespace("h", str(xhtml))
