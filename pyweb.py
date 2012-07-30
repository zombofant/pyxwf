#!/usr/bin/python2
# encoding=utf-8
from __future__ import unicode_literals, print_function

APPDIR = "/var/www/docroot/horazont/projects/pyweb"

import sys, os
sys.path.append("/var/www/docroot/horazont/projects/pyweb")
os.chdir(APPDIR)

import PyWeb.Stack
import PyWeb.Documents.PyWebXML

from PyWeb.utils import ET

import WebStack
from WebStack.Adapters.WSGI import WSGIAdapter

application = WSGIAdapter(PyWeb.Stack.WebStackSite("site/sitemap.xml"), handle_errors=0)
