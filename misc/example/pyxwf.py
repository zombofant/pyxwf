#!/usr/bin/python2
# encoding=utf-8
from __future__ import unicode_literals, print_function

import sys, os

# we keep our pyxwf instance configurations in /etc/webconf, which is set up as
# python package by adding an empty __init__.py. Each web project gets its own
# python module which contains a dict called ``conf``.
# See also site_name.py
sys.path.append("/etc")
from webconf.site_name import conf
sys.path.remove("/etc")

try:
    sys.path.extend(conf["pythonpath"])
except KeyError:
    pass
os.chdir(conf["datapath"])

import WebStack
from WebStack.Adapters.WSGI import WSGIAdapter
import PyXWF.Stack

sitemapFile = os.path.join(conf["datapath"], "sitemap.xml")

application = WSGIAdapter(PyXWF.Stack.WebStackSite(
	sitemapFile,
	defaultURLRoot=conf.get("urlroot")
    ),
    handle_errors=0
)
