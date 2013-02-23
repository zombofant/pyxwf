#!/usr/bin/python2
# encoding=utf-8
# File name: pyxwf.py
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
