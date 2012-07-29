#!/usr/bin/python2
# encoding=utf-8
from __future__ import unicode_literals, print_function

import PyWeb.Sitemap
import PyWeb.Nodes.Page
import PyWeb.Documents.PyWebXML

if __name__=="__main__":
    sm = PyWeb.Sitemap.Site(open("site/sitemap.xml", "r"))
    sm.render("/home").write(open("home.xhtml", "w"), encoding="utf-8", method="xml")
