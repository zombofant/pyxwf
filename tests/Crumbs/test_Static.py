# File name: test_Static.py
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
from __future__ import unicode_literals

import unittest

from PyXWF.utils import ET
import PyXWF.Errors as Errors
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Namespaces as NS

import PyXWF.Nodes.Page as Page

import PyXWF.Crumbs.Static as Static

import tests.Mocks as Mocks

class StaticCrumb(Mocks.DynamicSiteTest):
    test_doc_xml = """\
<?xml version="1.0" encoding="utf-8"?>
<page xmlns="{xmlns}">
    <meta></meta>
    <body xmlns="http://www.w3.org/1999/xhtml"><p>Content</p></body>
</page>""".format(xmlns=str(NS.PyWebXML)).encode("utf-8")

    def setUp(self):
        super(StaticCrumb, self).setUp()
        with self.fs.open("test-doc.xml", "wb") as f:
            f.write(self.test_doc_xml)

    def setUpSitemap(self, etree, meta, plugins, tweaks, tree, crumbs):
        ET.SubElement(tree, Page.PageNS.node, attrib={
            "src": "test-doc.xml",
            "type": ContentTypes.PyWebXML
        })
        ET.SubElement(crumbs, Static.StaticNS.crumb, attrib={
            "src": "test-doc.xml",
            "type": ContentTypes.PyWebXML,
            "id": "test"
        })

    def get_site(self, **kwargs):
        self.setup_site(self.get_sitemap(self.setUpSitemap, **kwargs))
        return self.site

    def get_crumb(self, **kwargs):
        self.get_site(**kwargs)
        crumb = self.site.crumbs["test"]
        self.ctx = Mocks.MockedContext.from_site(self.site)
        return crumb

    def test_init(self):
        node = ET.Element("crumb", attrib={})
        self.assertRaises(Errors.CrumbConfigurationError, Static.StaticCrumb, None, node)

        node.set("src", "non-existent.xml")
        node.set("type", ContentTypes.PyWebXML)
        site = self.get_site()
        self.assertRaises(IOError, Static.StaticCrumb, site, node)

    def test_render(self):
        crumb = self.get_crumb()
        node = ET.Element(NS.XHTML.body)
        for el in crumb.render(self.ctx, node):
            node.append(el)

        self.assertMultiLineEqual(
            ET.tostring(node, encoding="utf-8"),
            ET.tostring(
                NS.XHTML("body",
                    NS.XHTML("p", "Content")
                ),
                encoding="utf-8"
            )
        )

