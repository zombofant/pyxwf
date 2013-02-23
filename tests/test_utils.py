# File name: test_utils.py
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

import unittest, os
from datetime import datetime

import lxml.builder as builder

from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.TimeUtils as TimeUtils

import Mocks

class split_tag(unittest.TestCase):
    def test_split(self):
        tag = NS.XHTML.head
        ns, name = utils.split_tag(tag)
        self.assertEqual(ns, str(NS.XHTML))
        self.assertEqual(name, "head")

    def test_split_no_namespace(self):
        tag = "head"
        ns, name = utils.split_tag(tag)
        self.assertIsNone(ns)
        self.assertEqual(name, "head")

    def test_empty(self):
        tag = ""
        ns, name = utils.split_tag(tag)
        self.assertIsNone(ns)
        self.assertEqual(name, "")


class add_class(unittest.TestCase):
    def setUp(self):
        self.el = ET.Element(NS.XHTML.a)

    def test_first(self):
        el = self.el
        utils.add_class(el, "foo")
        self.assertEqual(el.get("class"), "foo")

    def test_second(self):
        el = self.el
        el.set("class", "bar")
        utils.add_class(el, "foo")
        self.assertEqual(set(el.get("class").split()), frozenset(("foo", "bar")))

    def test_two(self):
        el = self.el
        utils.add_class(el, "foo")
        utils.add_class(el, "bar")
        self.assertEqual(set(el.get("class").split()), frozenset(("foo", "bar")))

    def test_cleans(self):
        el = self.el
        el.set("class", "foo    ")
        utils.add_class(el, "bar")
        self.assertEqual(set(el.get("class").split()), frozenset(("foo", "bar")))

    def test_setish(self):
        el = self.el
        s = " ".join(frozenset(("foo", "bar")))
        el.set("class", s)
        utils.add_class(el, "bar")
        self.assertEqual(el.get("class"), s)

    def tearDown(self):
        del self.el


class unicode2xpathstr(unittest.TestCase):
    def test_convert(self):
        self.assertEqual('"foobar"', utils.unicode2xpathstr("foobar"))

    def test_escape(self):
        self.assertEqual(r'"\"foo\""', utils.unicode2xpathstr('"foo"'))


class parse_iso_date(unittest.TestCase):
    def test_none(self):
        self.assertIsNone(utils.parse_iso_date(None))

    def test_parse(self):
        dt = datetime(2012, 8, 25, 10, 8, 15)
        self.assertEqual(dt, utils.parse_iso_date("2012-08-25T10:08:15Z"))

    def test_requireZ(self):
        self.assertRaises(ValueError, utils.parse_iso_date, "2012-08-25T10:08:15")


class XHTMLToHTML(unittest.TestCase):
    def test_lxml_comparision(self):
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

    def test_valid_tree(self):
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

    def test_invalid_tree(self):
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


class file_last_modified(Mocks.FSTest):
    def setUp(self):
        super(file_last_modified, self).setUp()
        utils.file_last_modified = self.old_last_modified

    def test_non_existing(self):
        self.assertIsNone(utils.file_last_modified(os.path.join(self.fs.Root, "foo")))

    def test_file(self):
        path = self.fs("test.file")
        time = TimeUtils.now()
        f = open(path, "w")
        f.close()
        os.utime(path, (time, time))

        self.assertEqual(TimeUtils.to_datetime(time), utils.file_last_modified(path))
