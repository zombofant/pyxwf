# this is quite meta
from __future__ import unicode_literals

import os, unittest

import Mocks

class MockFSLocation(unittest.TestCase):
    def setUp(self):
        self.location = Mocks.MockFSLocation()

    def test_dirs(self):
        self.assertTrue(os.path.isdir(self.location.Root))

    def test_close(self):
        self.location.close()
        self.assertRaises(ValueError, getattr, self.location, "Root")

    def test___call__(self):
        path = "foo/bar"
        self.assertEqual(os.path.join(self.location.Root, path), self.location(path))

    def test_open(self):
        someFile = "foo.bar"
        f = self.location.open(someFile, "w")
        f.close()
        self.assertTrue(os.path.isfile(self.location(someFile)))

    def tearDown(self):
        self.location.close()
