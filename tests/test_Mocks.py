# this is quite meta
from __future__ import unicode_literals

import os, unittest

import Mocks

class MockFSLocation(unittest.TestCase):
    def setUp(self):
        self.location = Mocks.MockFSLocation()

    def test_dirs(self):
        self.assertTrue(os.path.isdir(self.location.Root))
        self.assertTrue(os.path.isdir(self.location.SiteDir))

    def test_close(self):
        self.location.close()
        self.assertRaises(ValueError, getattr, self.location, "Root")
        self.assertRaises(ValueError, getattr, self.location, "SiteDir")

    def tearDown(self):
        self.location.close()
