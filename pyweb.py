#!/usr/bin/python2
# encoding=utf-8
from __future__ import unicode_literals, print_function

import PyWeb.Sitemap
import PyWeb.Nodes.Page
import PyWeb.Nodes.Directory
import PyWeb.Nodes.Redirect
import PyWeb.Documents.PyWebXML

import xml.etree.ElementTree as ET

if __name__=="__main__":
    sm = PyWeb.Sitemap.Site(open("site/sitemap.xml", "r"))
    ET.ElementTree(sm.render("").body).write(open("home.xhtml", "w"), encoding="utf-8", method="xml")
