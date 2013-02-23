# File name: test_Namespaces.py
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
import PyXWF.Namespaces as NS

import tests.Mocks as Mocks

class Metaclass(unittest.TestCase):
    def setUp(self):
        self.ns = str(Mocks.MockNS)
        self.mcls = NS.__metaclass__(b"unit-testing-class",
            (object, ),
            {
                "xmlns": self.ns
            }
        )

    def test___str__(self):
        self.assertEqual(str(self.mcls), self.ns)

    def test___unicode__(self):
        self.assertEqual(unicode(self.mcls), self.ns)

    def test___getattr__(self):
        self.assertEqual(self.mcls.foo, "{{{0}}}foo".format(self.ns))

    def test___call__(self):
        el = ET.Element(self.mcls.foo)
        self.assertEqual(ET.tostring(el), ET.tostring(self.mcls("foo")))

    def tearDown(self):
        del self.mcls
