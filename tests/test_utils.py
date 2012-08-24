from __future__ import unicode_literals

import unittest, os
from datetime import datetime

import lxml.builder as builder

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.TimeUtils as TimeUtils

import Mocks

class splitTag(unittest.TestCase):
    def test_split(self):
        tag = NS.XHTML.head
        ns, name = utils.splitTag(tag)
        self.assertEqual(ns, str(NS.XHTML))
        self.assertEqual(name, "head")

    def test_splitNoNS(self):
        tag = "head"
        ns, name = utils.splitTag(tag)
        self.assertIsNone(ns)
        self.assertEqual(name, "head")

    def test_empty(self):
        tag = ""
        ns, name = utils.splitTag(tag)
        self.assertIsNone(ns)
        self.assertEqual(name, "")


class addClass(unittest.TestCase):
    def setUp(self):
        self.el = ET.Element(NS.XHTML.a)

    def test_first(self):
        el = self.el
        utils.addClass(el, "foo")
        self.assertEqual(el.get("class"), "foo")

    def test_second(self):
        el = self.el
        el.set("class", "bar")
        utils.addClass(el, "foo")
        self.assertEqual(set(el.get("class").split()), frozenset(("foo", "bar")))

    def test_two(self):
        el = self.el
        utils.addClass(el, "foo")
        utils.addClass(el, "bar")
        self.assertEqual(set(el.get("class").split()), frozenset(("foo", "bar")))

    def test_cleans(self):
        el = self.el
        el.set("class", "foo    ")
        utils.addClass(el, "bar")
        self.assertEqual(set(el.get("class").split()), frozenset(("foo", "bar")))

    def test_setish(self):
        el = self.el
        s = " ".join(frozenset(("foo", "bar")))
        el.set("class", s)
        utils.addClass(el, "bar")
        self.assertEqual(el.get("class"), s)

    def tearDown(self):
        del self.el


class unicodeToXPathStr(unittest.TestCase):
    def test_convert(self):
        self.assertEqual('"foobar"', utils.unicodeToXPathStr("foobar"))

    def test_escape(self):
        self.assertEqual(r'"\"foo\""', utils.unicodeToXPathStr('"foo"'))


class parseISODate(unittest.TestCase):
    def test_none(self):
        self.assertIsNone(utils.parseISODate(None))

    def test_parse(self):
        dt = datetime(2012, 8, 25, 10, 8, 15)
        self.assertEqual(dt, utils.parseISODate("2012-08-25T10:08:15Z"))

    def test_requireZ(self):
        self.assertRaises(ValueError, utils.parseISODate, "2012-08-25T10:08:15")


class XHTMLToHTML(unittest.TestCase):
    def test_lxmlComparision(self):
        xhtml = NS.XHTML
        treeA = xhtml("html",
            xhtml("head",
                xhtml("title", "foobar")
            ),
            xhtml("body",
                xhtml("p", "some text")
            )
        )
        treeC = xhtml("html",
            xhtml("head",
                xhtml("title", "foobar")
            ),
            xhtml("body",
                xhtml("p", "some text")
            )
        )
        treeB = xhtml("html",
            xhtml("head",
                xhtml("title", "foobar")
            ),
            xhtml("body",
                xhtml("p", "some _other_ text")
            )
        )
        self.assertNotEqual(ET.tostring(treeA), ET.tostring(treeB))
        self.assertEqual(ET.tostring(treeA), ET.tostring(treeC))

    def test_validTree(self):
        title = "foobar"
        text = "some text"

        html = builder.E
        xhtml = NS.XHTML
        tree = xhtml("html",
            xhtml("head",
                xhtml("title", title)
            ),
            xhtml("body",
                xhtml("p", text)
            )
        )
        utils.XHTMLToHTML(tree)
        self.assertEqual(ET.tostring(tree), ET.tostring(html.html(
            html.head(
                html.title(title)
            ),
            html.body(
                html.p(text)
            )
        )))

    def test_invalidTree(self):
        title = "foobar"
        text = "some text"

        xhtml = NS.XHTML
        tree = xhtml("html",
            xhtml("head",
                xhtml("title", title)
            ),
            xhtml("body",
                xhtml("p", text),
                NS.PyWebXML("a", "some link")
            )
        )
        self.assertRaises(ValueError, utils.XHTMLToHTML, tree)


class fileLastModified(Mocks.FSTest):
    def test_nonExisting(self):
        self.assertIsNone(utils.fileLastModified(os.path.join(self.fs.Root, "foo")))

    def test_file(self):
        path = self.fs("test.file")
        time = TimeUtils.now()
        f = open(path, "w")
        f.close()
        os.utime(path, (time, time))

        self.assertEqual(TimeUtils.toDatetime(time), utils.fileLastModified(path))
