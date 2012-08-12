#!/usr/bin/python2
# encoding=utf-8
from __future__ import unicode_literals, print_function

import sys, os

sys.path.append("/etc")
from webconf.pyweb import conf
sys.path.remove("/etc")

try:
    sys.path.extend(conf["pythonpath"])
except KeyError:
    pass
os.chdir(conf["datapath"])

import WebStack
from WebStack.Adapters.WSGI import WSGIAdapter
import PyWeb.Stack

sitemapFile = os.path.join(conf["datapath"], "sitemap.xml")

application = WSGIAdapter(PyWeb.Stack.WebStackSite(
	sitemapFile,
	defaultURLRoot=conf.get("urlroot")
    ),
    handle_errors=0
)
