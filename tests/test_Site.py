from __future__ import unicode_literals

import unittest

from PyXWF.utils import ET
import PyXWF.Namespaces as NS
import PyXWF.ContentTypes as ContentTypes
import PyXWF.Message as Message

import PyXWF.Nodes.Page

import Mocks

class SimpleSite(Mocks.SiteTest):
    def setUpFS(self):
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
        self._rootNode = self.site.tree.index

    def test_transformHref_relative(self):
        el = NS.XHTML("a")
        el.set("href", "foo/bar")
        self.site.transformHref(None, el)
        self.assertEqual(el.get("href"), "/foo/bar")

    def test_transformHref_absolute(self):
        el = NS.XHTML("a")
        el.set("href", "/foo/bar")
        # invariance on absolute paths
        self.site.transformHref(None, el)
        self.assertEqual(el.get("href"), "/foo/bar")

    def test_transformHref_absoluteURI(self):
        uri = "xmpp:foobar@example.com"
        el = NS.XHTML("a")
        el.set("href", uri)
        self.site.transformHref(None, el)
        self.assertEqual(el.get("href"), uri)

    def test_transformHref_toURI(self):
        ctx = Mocks.MockedContext.fromSite(self.site)
        el = NS.XHTML("a")
        el.set("href", "foo/bar")
        self.site.transformHref(ctx, el, makeGlobal=True)
        self.assertEqual(el.get("href"), "{0}://{1}/foo/bar".format(ctx.URLScheme, ctx.HostName))

    def test__getNode(self):
        ctx = Mocks.MockedContext.fromSite(self.site)
        self.assertIs(self.site._getNode(ctx), self._rootNode)

    def test_getNode(self):
        self.assertIs(self.site.getNode("home"), self._rootNode)
        self.assertRaises(KeyError, self.site.getNode, "invalid-id")

    def test_getMessage_xhtml(self):
        ctx = Mocks.MockedContext.fromSite(self.site)
        message = self.site.getMessage(ctx)
        xhtml = NS.XHTML
        refMessage = Message.XHTMLMessage(xhtml("html",
            xhtml("head",
                xhtml("title", "Home"),
            ),
            xhtml("body",
                xhtml("p", "some text")
            )
        ), encoding="utf-8")
        self.assertEqual(message, refMessage)
        ctx = Mocks.MockedContext.fromSite(self.site,
                accept="text/html, application/xhtml+xml")
        message = self.site.getMessage(ctx)
        self.assertEqual(message, refMessage)

    def test_getMessage_html(self):
        ctx = Mocks.MockedContext.fromSite(self.site, accept="text/html")
        message = self.site.getMessage(ctx)
        xhtml = NS.XHTML
        refMessage = Message.HTMLMessage.fromXHTMLTree(xhtml("html",
            xhtml("head",
                xhtml("title", "Home"),
            ),
            xhtml("body",
                xhtml("p", "some text")
            )
        ), encoding="utf-8")
        self.assertEqual(message, refMessage)
        ctx = Mocks.MockedContext.fromSite(self.site,
                accept="text/html, application/xhtml+xml;q=0.9")
        message = self.site.getMessage(ctx)
        self.assertEqual(message, refMessage)

