from __future__ import unicode_literals

import unittest

from PyXWF.utils import ET
import PyXWF.Errors as Errors
import PyXWF.Namespaces as NS

import PyXWF.Nodes.Transform as Transform

import tests.Mocks as Mocks


class TransformNode(Mocks.DynamicSiteTest):
    data_values = ["bar", "baz", "quux"]

    data_xml = """\
<?xml version="1.0" encoding="utf-8" ?>
<data>
    {}
</data>
""".format(["<foo>{}</foo>".format(value) for value in data_values]).encode("utf-8")

    transform_xml = """\
<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet
        version='1.0'
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
        xmlns:a="http://pyxwf.zombofant.net/xmlns/templates/default">
    <xsl:output method="xml" encoding="utf-8" />

    <xsl:template match="/data">
        <py:page>
            <py:meta>
                <h:script src="html_script" />
                <py:script href="py_script" />
            </py:meta>
            <body xmlns="http://www.w3.org/1999/xhtml">
                <ul>
                    <xsl:for-each select="foo">
                        <li><xsl:value-of select="." /></li>
                    </xsl:for-each>
                </ul>
            </body>
        </py:page>
    </xsl:template>

</xsl:stylesheet>
""".encode("utf-8")

    def setUpSitemap(self, etree, meta, plugins, tweaks, tree, crumbs):
        trafo = ET.SubElement(tree, Transform.TransformNS.node, attrib={
            "name": "",
            "src": "data.xml",
            "transform": "transform.xsl",
            "nav-title": "foo",
        })

    def get_transform(self):
        self.setup_site(self.get_sitemap(self.setUpSitemap))
        transform = self.site.tree.index
        self.ctx = Mocks.MockedContext.from_site(self.site)
        return transform

    def setUp(self):
        super(TransformNode, self).setUp()
        with self.fs.open("data.xml", "wb") as f:
            f.write(self.data_xml)
        with self.fs.open("transform.xsl", "wb") as f:
            f.write(self.transform_xml)

    def test_meta_xml_valid(self):
        ET.XML(self.data_xml)
        ET.XML(self.transform_xml)
        ET.XSLT(ET.XML(self.transform_xml))

    def test_complete_transform(self):
        trafo = self.get_transform()
        response = self.site.get_message(self.ctx)

        ul_children = [NS.XHTML("li", value) for value in self.data_values]

        correct_tree = NS.XHTML("html",
            NS.XHTML("head",
                NS.XHTML("title", "None"),
                NS.XHTML("script", src="html_script"),
                NS.XHTML("script", src="/py_script"),
            ),
            NS.XHTML("body",
                NS.XHTML("ul", *ul_children)
            )
        )
        self.maxDiff = None
        self.assertMultiLineEqual(ET.tostring(response.DocTree), ET.tostring(correct_tree))
