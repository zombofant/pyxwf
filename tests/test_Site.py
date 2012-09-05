from __future__ import unicode_literals

import unittest

from PyXWF.utils import ET
import PyXWF.Namespaces as NS
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Message as Message

import PyXWF.Nodes.Page

import Mocks

class SimpleSite(Mocks.SiteTest):
    def setup_fs(self):
        f = self.fs.open("basic.xml", "w")
        f.write("""<?xml version="1.0" ?>
<page   xmlns="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:a="http://pyxwf.zombofant.net/xmlns/templates/default">
    <meta>
        <title>Home</title>
    </meta>
    <body xmlns="http://www.w3.org/1999/xhtml">
        <p>some text</p>
    </body>
</page>
""")
        f.close()

        f = self.fs.open("basic.xsl", "w")
        f.write("""<?xml version="1.0" encoding="utf-8" ?>
<xsl:stylesheet
        version='1.0'
        xmlns:h="http://www.w3.org/1999/xhtml"
        xmlns:py="http://pyxwf.zombofant.net/xmlns/documents/pywebxml"
        xmlns:xsl='http://www.w3.org/1999/XSL/Transform'
        xmlns:a="http://pyxwf.zombofant.net/xmlns/templates/default">
    <xsl:output method="xml" encoding="utf-8" />

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="py:page">
        <py:page>
            <py:meta>
                <py:title><xsl:value-of select="$doc_title" /></py:title>
            </py:meta>
            <body xmlns="http://www.w3.org/1999/xhtml">
                <xsl:apply-templates select="h:body/*" />
            </body>
        </py:page>
    </xsl:template>
</xsl:stylesheet>""")
        f.close()

    def setUpSitemap(self, etree, meta, plugins, tweaks, tree, crumbs):
        node = ET.SubElement(tree, PyXWF.Nodes.Page.PageNS.node)
        node.set("src", "basic.xml")
        node.set("type", ContentTypes.PyWebXML)
        node.set("id", "home")

        tree.set("template", "basic.xsl")

    def setUp(self):
        super(SimpleSite, self).setUp()
        self._rootnode = self.site.tree.index

    def test_transform_href_relative(self):
        el = NS.XHTML("a")
        el.set("href", "foo/bar")
        self.site.transform_href(None, el)
        self.assertEqual(el.get("href"), "/foo/bar")

    def test_transform_href_absolute(self):
        el = NS.XHTML("a")
        el.set("href", "/foo/bar")
        # invariance on absolute paths
        self.site.transform_href(None, el)
        self.assertEqual(el.get("href"), "/foo/bar")

    def test_transform_href_absolute_URI(self):
        uri = "xmpp:foobar@example.com"
        el = NS.XHTML("a")
        el.set("href", uri)
        self.site.transform_href(None, el)
        self.assertEqual(el.get("href"), uri)

    def test_transform_href_to_URI(self):
        ctx = Mocks.MockedContext.from_site(self.site)
        el = NS.XHTML("a")
        el.set("href", "foo/bar")
        self.site.transform_href(ctx, el, make_global=True)
        self.assertEqual(el.get("href"), "{0}://{1}/foo/bar".format(ctx.URLScheme, ctx.HostName))

    def test__get_node(self):
        ctx = Mocks.MockedContext.from_site(self.site)
        self.assertIs(self.site._get_node(ctx), self._rootnode)

    def test_get_node(self):
        self.assertIs(self.site.get_node("home"), self._rootnode)
        self.assertRaises(KeyError, self.site.get_node, "invalid-id")

    def test_get_message_xhtml(self):
        ctx = Mocks.MockedContext.from_site(self.site)
        message = self.site.get_message(ctx)
        xhtml = NS.XHTML
        refmessage = Message.XHTMLMessage(xhtml("html",
            xhtml("head",
                xhtml("title", "Home"),
            ),
            xhtml("body",
                xhtml("p", "some text")
            )
        ), encoding="utf-8")
        self.assertEqual(message, refmessage)

        # test that XHTML is picked if both are equally accepted by the client
        ctx = Mocks.MockedContext.from_site(self.site,
                accept="text/html, application/xhtml+xml")
        message = self.site.get_message(ctx)
        self.assertEqual(message, refmessage)

        ctx = Mocks.MockedContext.from_site(self.site,
                accept="text/plain, text/html;q=0.8, application/xhtml+xml;q=0.8")
        message = self.site.get_message(ctx)
        self.assertEqual(message, refmessage)

    def test_get_message_html(self):
        ctx = Mocks.MockedContext.from_site(self.site, accept="text/html")
        message = self.site.get_message(ctx)
        xhtml = NS.XHTML
        refmessage = Message.HTMLMessage.from_xhtml_tree(xhtml("html",
            xhtml("head",
                xhtml("title", "Home"),
            ),
            xhtml("body",
                xhtml("p", "some text")
            )
        ), encoding="utf-8")
        self.assertEqual(message, refmessage)

        # test that HTML is picked if it is preferred by the client
        ctx = Mocks.MockedContext.from_site(self.site,
                accept="text/html, application/xhtml+xml;q=0.9")
        message = self.site.get_message(ctx)
        self.assertEqual(message, refmessage)

        ctx = Mocks.MockedContext.from_site(self.site,
                accept="text/plain, text/html;q=0.95, application/xhtml+xml;q=0.9")
        message = self.site.get_message(ctx)
        self.assertEqual(message, refmessage)

