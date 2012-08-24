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
