from __future__ import unicode_literals

import unittest

from PyWeb.utils import ET
import PyWeb.Namespaces as NS

class Metaclass(unittest.TestCase):
    ns = "http://pyweb.zombofant.net/xmlns/for-unit-testing-only"

    def setUp(self):
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
