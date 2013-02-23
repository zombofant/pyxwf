#!/usr/bin/python2
# File name: test_prefixless_xhtml.py
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
from __future__ import unicode_literals, print_function, absolute_import

import unittest
import os
import copy

import PyXWF
from PyXWF.utils import ET
import PyXWF.utils as utils
import PyXWF.Namespaces as NS
import PyXWF.Templates as Templates
import PyXWF.ContentTypes as ContentTypes

import tests.Mocks as Mocks

class PrefixlessXHTML(Mocks.SiteTest):
    def setUp(self):
        super(PrefixlessXHTML, self).setUp()
        transform_path = os.path.join(PyXWF.data_path, "prefixless-xhtml.xsl")
        self.transform = Templates.XSLTTemplate(self.site, transform_path)
        self.maxDiff = None

    def test_remove_prefix(self):
        test_xml = """<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<h:html xmlns:h="http://www.w3.org/1999/xhtml" xmlns:ml="http://foo">
  <h:head>
    <h:title>MathJax Test Page</h:title>
    <h:script type="text/javascript"><![CDATA[
      function test() {
        alert(document.getElementsByTagName("p").length);
      };
    ]]></h:script>
  </h:head>
  <h:body onload="test();">
    <h:p>test</h:p>
    <ml:foo></ml:foo>
  </h:body>
</h:html>""".encode("utf-8")

        result_xml = """<?xml version='1.0' encoding='utf-8'?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>MathJax Test Page</title>
    <script type="text/javascript">
      function test() {
        alert(document.getElementsByTagName("p").length);
      };
    </script>
  </head>
  <body onload="test();">
    <p>test</p>
    <ml:foo xmlns:ml="http://foo"/>
  </body>
</html>
""".encode("utf-8")

        self.assertMultiLineEqual(result_xml, ET.tostring(
            self.transform.raw_transform(ET.fromstring(test_xml), {}),
            pretty_print=True,
            encoding="utf-8",
            xml_declaration=True,
            doctype="<!DOCTYPE html>"
        ))
