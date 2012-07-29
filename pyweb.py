#!/usr/bin/python2
# encoding=utf-8
from __future__ import unicode_literals, print_function

import PyWeb.Sitemap
import PyWeb.Nodes.Page
import PyWeb.Nodes.Directory
import PyWeb.Nodes.Redirect
import PyWeb.Documents.PyWebXML

from PyWeb.utils import ET

import sys

if __name__=="__main__":
    sm = PyWeb.Sitemap.Site(open("site/sitemap.xml", "r"))
    print(ET.tostring(sm.render(sys.argv[1]), encoding="utf-8", method="xml", xml_declaration=True, doctype="<!DOCTYPE html>"))
