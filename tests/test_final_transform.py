#!/usr/bin/python2
from __future__ import unicode_literals, print_function, absolute_import

import unittest
import os
import copy

import PyXWF
from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.Templates as Templates

import tests.Mocks as Mocks

class FinalTransform(Mocks.SiteTest):
    def setUp(self):
        super(FinalTransform, self).setUp()
        transform_path = os.path.join(PyXWF.data_path, "final-transform.xsl")
        self.transform = Templates.XSLTTemplate(None, transform_path)
        self.maxDiff = None

    def mock_ctx(self):
        return Mocks.MockedContext(self.site.urlroot)

    def base_tree(self):
        root = NS.XHTML("html")
        head = ET.SubElement(root, NS.XHTML.head)
        body = ET.SubElement(root, NS.XHTML.body)
        return root, head, body

    def py_transform(self, body, ctx=None):
        ctx = ctx or self.mock_ctx()
        tree_py = copy.deepcopy(body)
        tree_py = self.site.transform_py_namespace(ctx, tree_py)
        return tree_py

    def raw_transform(self, body, ctx=None):
        ctx = ctx or self.mock_ctx()
        d = self.site.get_template_arguments(ctx)
        d[b"localr_prefix"] = utils.unicode2xpathstr(self.site.urlroot)
        d[b"host_prefix"] = utils.unicode2xpathstr(
            "{0}://{1}".format(
                ctx.URLScheme,
                ctx.HostName
            )
        )
        d[b"deliver_mobile"] = str(ctx.IsMobileClient).lower()
        return self.transform.raw_transform(body, d)

    def assertTreeEqual(self, tree_a, tree_b):
        ET.cleanup_namespaces(tree_a)
        ET.cleanup_namespaces(tree_b)
        self.assertMultiLineEqual(
            ET.tostring(tree_a),
            ET.tostring(tree_b),
        )

    def test_legacy_a_and_img(self):
        root, _, body = self.base_tree()
        a = ET.SubElement(body, NS.PyWebXML.a)
        a.set("href", "foobar/baz")
        a.tail = "\n"
        a = ET.SubElement(body, NS.PyWebXML.a)
        a.set("href", "/foobar/baz")
        a.tail = "\n"
        img = ET.SubElement(body, NS.PyWebXML.img)
        img.set("href", "foobar/baz")
        img.tail = "\n"
        img = ET.SubElement(body, NS.PyWebXML.img)
        img.set("href", "/foobar/baz")
        img.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)
        tree_py = self.py_transform(root, ctx=ctx)
        self.assertTreeEqual(tree_xsl, tree_py)

    def test_legacy_py_content(self):
        root, _, body = self.base_tree()
        div = ET.SubElement(body, NS.XHTML.div)
        div.set(NS.PyWebXML.content, "foobar/baz")
        div.set(getattr(NS.PyWebXML, "content-make-uri"), "true")
        div.tail = "\n"
        div = ET.SubElement(body, NS.XHTML.div)
        div.set(NS.PyWebXML.content, "/foobar/baz")
        div.set(getattr(NS.PyWebXML, "content-make-uri"), "true")
        div.tail = "\n"
        div = ET.SubElement(body, NS.XHTML.div)
        div.set(NS.PyWebXML.content, "foobar/baz")
        div.tail = "\n"
        div = ET.SubElement(body, NS.XHTML.div)
        div.set(NS.PyWebXML.content, "/foobar/baz")
        div.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)
        tree_py = self.py_transform(root, ctx=ctx)
        self.assertTreeEqual(tree_xsl, tree_py)

    def test_legacy_link(self):
        root, head, _ = self.base_tree()
        link = ET.SubElement(head, NS.PyWebXML.link)
        link.set("href", "/foobar/baz")
        link.tail = "\n"
        link = ET.SubElement(head, NS.PyWebXML.link)
        link.set("href", "foobar/baz")
        link.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)
        tree_py = self.py_transform(root, ctx=ctx)
        self.assertTreeEqual(tree_xsl, tree_py)

    def test_legacy_py_mobile(self):
        root, _, body = self.base_tree()
        if_mobile_true = ET.SubElement(body, getattr(NS.PyWebXML, "if-mobile"))
        ET.SubElement(if_mobile_true, NS.XHTML.div)
        if_mobile_false = ET.SubElement(body, getattr(NS.PyWebXML, "if-mobile"))
        if_mobile_false.set("mobile", "false")
        ET.SubElement(if_mobile_false, NS.XHTML.span)

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)
        tree_py = self.py_transform(root, ctx=ctx)
        self.assertTreeEqual(tree_xsl, tree_py)

    def test_drop_empty(self):
        root, _, body = self.base_tree()
        drop_empty = ET.SubElement(body, NS.XHTML.div)
        drop_empty.set(getattr(NS.PyWebXML, "drop-empty"), "true")

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)
        tree_py = self.py_transform(root, ctx=ctx)
        self.assertTreeEqual(tree_xsl, tree_py)

    def test_localr(self):
        root, _, body = self.base_tree()
        div1 = ET.SubElement(body, NS.XHTML.div)
        div1.set(NS.LocalR.content, "foobar/baz")
        div1.tail = "\n"
        div2 = ET.SubElement(body, NS.XHTML.div)
        div2.set(NS.LocalR.content, "/foobar/baz")
        div2.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)

        div1.set("content", "/foobar/baz")
        del div1.attrib[NS.LocalR.content]
        div2.set("content", "/foobar/baz")
        del div2.attrib[NS.LocalR.content]

        self.assertTreeEqual(tree_xsl, root)

    def test_localg(self):
        root, _, body = self.base_tree()
        div3 = ET.SubElement(body, NS.XHTML.div)
        div3.set(NS.LocalG.content, "foobar/baz")
        div3.tail = "\n"
        div4 = ET.SubElement(body, NS.XHTML.div)
        div4.set(NS.LocalG.content, "/foobar/baz")
        div4.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)
        div3.set("content", "{0}://{1}/foobar/baz".format(ctx.URLScheme, ctx.HostName))
        del div3.attrib[NS.LocalG.content]
        div4.set("content", "{0}://{1}/foobar/baz".format(ctx.URLScheme, ctx.HostName))
        del div4.attrib[NS.LocalG.content]

        self.assertTreeEqual(tree_xsl, root)

    def tearDown(self):
        del self.transform
        super(FinalTransform, self).tearDown()
