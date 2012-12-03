#!/usr/bin/python2
# encoding=utf-8
from __future__ import unicode_literals, print_function

import sys
import os
import logging

# you can configure logging here as you wish. This is the recommended
# configuration for testing (disable DEBUG-logging on the cache, it's rather
# verbose and not particularily helpful at the start)
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("PyXWF.Cache").setLevel(logging.INFO)

conf = {
    "pythonpath": ["."],
    "datapath": os.path.join(os.getcwd(), "examples/start"),
    "urlroot": "/"
}

try:
    sys.path.extend(conf["pythonpath"])
except KeyError:
    pass
os.chdir(conf["datapath"])

import PyXWF.WebBackends.WSGI as WSGI

sitemapFile = os.path.join(conf["datapath"], "sitemap.xml")

application = WSGI.WSGISite(
    sitemapFile,
    default_url_root=conf.get("urlroot")
)
