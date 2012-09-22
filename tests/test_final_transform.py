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

    def replace_py_content(self, node, new_value):
        node.set("content", new_value)
        del node.attrib[NS.PyWebXML.content]
        content_uri_attr = getattr(NS.PyWebXML, "content-make-uri")
        if content_uri_attr in node.attrib:
            del node.attrib[content_uri_attr]

    def test_a_and_img(self):
        root, _, body = self.base_tree()
        a1 = ET.SubElement(body, NS.PyWebXML.a)
        a1.set("href", "foobar/baz")
        a1.tail = "\n"
        a2 = ET.SubElement(body, NS.PyWebXML.a)
        a2.set("href", "/foobar/baz")
        a2.tail = "\n"
        img1 = ET.SubElement(body, NS.PyWebXML.img)
        img1.set("href", "foobar/baz")
        img1.tail = "\n"
        img2 = ET.SubElement(body, NS.PyWebXML.img)
        img2.set("href", "/foobar/baz")
        img2.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)

        a1.tag = NS.XHTML.a
        a1.set("href", "/foobar/baz")
        a2.tag = NS.XHTML.a
        img1.tag = NS.XHTML.img
        img1.set("src", "/foobar/baz")
        del img1.attrib["href"]
        img2.tag = NS.XHTML.img
        img2.set("src", "/foobar/baz")
        del img2.attrib["href"]

        self.assertTreeEqual(tree_xsl, root)

    def test_py_content(self):
        root, _, body = self.base_tree()
        div1 = ET.SubElement(body, NS.XHTML.div)
        div1.set(NS.PyWebXML.content, "foobar/baz")
        div1.set(getattr(NS.PyWebXML, "content-make-uri"), "true")
        div1.tail = "\n"
        div2 = ET.SubElement(body, NS.XHTML.div)
        div2.set(NS.PyWebXML.content, "/foobar/baz")
        div2.set(getattr(NS.PyWebXML, "content-make-uri"), "true")
        div2.tail = "\n"
        div3 = ET.SubElement(body, NS.XHTML.div)
        div3.set(NS.PyWebXML.content, "foobar/baz")
        div3.tail = "\n"
        div4 = ET.SubElement(body, NS.XHTML.div)
        div4.set(NS.PyWebXML.content, "/foobar/baz")
        div4.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)

        uri = "{0}://{1}/foobar/baz".format(
            ctx.URLScheme,
            ctx.HostName
        )
        self.replace_py_content(div1, uri)
        self.replace_py_content(div2, uri)
        self.replace_py_content(div3, "/foobar/baz")
        self.replace_py_content(div4, "/foobar/baz")

        self.assertTreeEqual(tree_xsl, root)

    def test_link(self):
        root, head, _ = self.base_tree()
        link1 = ET.SubElement(head, NS.PyWebXML.link)
        link1.set("href", "/foobar/baz")
        link1.tail = "\n"
        link2 = ET.SubElement(head, NS.PyWebXML.link)
        link2.set("href", "foobar/baz")
        link2.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)

        link1.tag = NS.XHTML.link
        link2.tag = NS.XHTML.link
        link2.set("href", "/foobar/baz")

        self.assertTreeEqual(tree_xsl, root)

    def test_py_mobile(self):
        root, _, body = self.base_tree()
        if_mobile_true = ET.SubElement(body, getattr(NS.PyWebXML, "if-mobile"))
        ET.SubElement(if_mobile_true, NS.XHTML.div)
        if_mobile_false1 = ET.SubElement(body, getattr(NS.PyWebXML, "if-mobile"))
        if_mobile_false1.set("mobile", "false")
        if_mobile_false1.set("id", "baz")
        ET.SubElement(if_mobile_false1, NS.XHTML.span)
        if_mobile_false2 = ET.SubElement(body, getattr(NS.PyWebXML, "if-mobile"))
        if_mobile_false2.set("mobile", "false")
        if_mobile_false2.set("xhtml-element", "div")
        if_mobile_false2.set("class", "bar")
        ET.SubElement(if_mobile_false2, NS.XHTML.span)

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)

        body.remove(if_mobile_true)
        if_mobile_false1.tag = NS.XHTML.span
        del if_mobile_false1.attrib["mobile"]
        if_mobile_false2.tag = NS.XHTML.div
        del if_mobile_false2.attrib["mobile"]
        del if_mobile_false2.attrib["xhtml-element"]

        self.assertTreeEqual(tree_xsl, root)

    def test_drop_empty(self):
        root, _, body = self.base_tree()
        drop_empty1 = ET.SubElement(body, NS.XHTML.div)
        drop_empty1.set(getattr(NS.PyWebXML, "drop-empty"), "true")
        drop_empty1.set("class", "foo")
        drop_empty2 = ET.SubElement(body, NS.XHTML.div)
        drop_empty2.set(getattr(NS.PyWebXML, "drop-empty"), "true")
        drop_empty2.set("class", "foo")
        drop_empty2.set("id", "bar")
        ET.SubElement(drop_empty2, NS.XHTML.a)

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)

        body.remove(drop_empty1)
        del drop_empty2.attrib[getattr(NS.PyWebXML, "drop-empty")]

        self.assertTreeEqual(tree_xsl, root)

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

    def test_mixed(self):
        root, _, body = self.base_tree()
        body.text = "\n"
        a = ET.SubElement(body, NS.PyWebXML.a)
        a.set("href", "foobar/baz")
        a.set(NS.PyWebXML.content, "foobar/baz")
        a.tail = "\n"

        ctx = self.mock_ctx()
        tree_xsl = self.raw_transform(root, ctx=ctx)

        a.tag = NS.XHTML.a
        a.set("href", "/foobar/baz")
        a.set("content", "/foobar/baz")
        del a.attrib[NS.PyWebXML.content]

        self.assertTreeEqual(tree_xsl, root)

    def tearDown(self):
        del self.transform
        super(FinalTransform, self).tearDown()
